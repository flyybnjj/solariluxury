import logging
import random
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
import json
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.http import url_has_allowed_host_and_scheme

from catalogo.models import PreOrden, Pedido, Tracker
from .models import Cliente, OtpChallenge, OtpRateLimit, TicketSoporte
from .forms import CustomerPasswordResetForm, LoginForm, PasswordResetCodeForm, RegistroForm
from .utils import enviar_cupon_bienvenida

logger = logging.getLogger(__name__)

def legacy_pin_redirect(request):
    messages.info(request, 'El acceso ahora es con correo o usuario y contraseña. Si no la recuerdas, usa “Recuperar contraseña”.')
    return redirect('login')


PASSWORD_RESET_CODE_TTL = timedelta(minutes=10)
PASSWORD_RESET_CODE_MAX_ATTEMPTS = 5
PASSWORD_RESET_CHALLENGE_SESSION_KEY = 'password_reset_challenge_id'
PASSWORD_RESET_VERIFIED_SESSION_KEY = 'password_reset_verified_challenge_id'


def _allow_password_reset_request(kind, subject, now):
    normalized_subject = subject.strip().lower()
    subject_hash = salted_hmac(
        f'password-reset:{kind}', normalized_subject, secret=settings.SECRET_KEY
    ).hexdigest()
    defaults = {
        'window_started_at': now,
        'last_requested_at': now - timedelta(seconds=61),
        'requests_count': 0,
    }
    with transaction.atomic():
        limiter, _ = OtpRateLimit.objects.get_or_create(
            kind=kind, subject_hash=subject_hash, defaults=defaults
        )
        limiter = OtpRateLimit.objects.select_for_update().get(pk=limiter.pk)
        if now - limiter.window_started_at >= timedelta(hours=1):
            limiter.window_started_at = now
            limiter.requests_count = 0
        if limiter.requests_count >= 5 or now - limiter.last_requested_at < timedelta(seconds=60):
            limiter.save(update_fields=['window_started_at', 'requests_count'])
            return False
        limiter.last_requested_at = now
        limiter.requests_count += 1
        limiter.save(update_fields=['window_started_at', 'last_requested_at', 'requests_count'])
    return True


@never_cache
def password_reset_request(request):
    form = CustomerPasswordResetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        now = timezone.now()
        remote_ip = request.META.get('REMOTE_ADDR', '') or 'unknown'
        allowed_by_email = _allow_password_reset_request(OtpRateLimit.EMAIL, email, now)
        allowed_by_ip = _allow_password_reset_request(OtpRateLimit.IP, remote_ip, now)

        if allowed_by_email and allowed_by_ip:
            users = list(form.get_users(email))
            if len(users) == 1:
                code = f'{secrets.randbelow(1_000_000):06d}'
                with transaction.atomic():
                    OtpChallenge.objects.filter(
                        email__iexact=email, consumed_at__isnull=True
                    ).update(consumed_at=now)
                    challenge = OtpChallenge.objects.create(
                        email=email,
                        pin_hash=make_password(code),
                        expires_at=now + PASSWORD_RESET_CODE_TTL,
                    )

                request.session[PASSWORD_RESET_CHALLENGE_SESSION_KEY] = challenge.pk
                request.session.pop(PASSWORD_RESET_VERIFIED_SESSION_KEY, None)
                request.session.set_expiry(15 * 60)
                context = {'codigo': code, 'minutos_expiracion': 10}
                try:
                    message = EmailMultiAlternatives(
                        subject=render_to_string(
                            'usuarios/password_reset/password_reset_subject.txt', context
                        ).strip(),
                        body=render_to_string(
                            'usuarios/password_reset/password_reset_email.txt', context
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                    )
                    message.attach_alternative(
                        render_to_string(
                            'usuarios/password_reset/password_reset_email.html', context
                        ),
                        'text/html',
                    )
                    sent_count = message.send(fail_silently=False)
                    if sent_count != 1:
                        raise RuntimeError('SMTP did not accept the password reset message')
                except Exception as exc:
                    OtpChallenge.objects.filter(pk=challenge.pk).update(consumed_at=timezone.now())
                    request.session.pop(PASSWORD_RESET_CHALLENGE_SESSION_KEY, None)
                    request.session.pop(PASSWORD_RESET_VERIFIED_SESSION_KEY, None)
                    logger.error('Password reset email failed: exception=%s', type(exc).__name__)
                    messages.error(request, 'No pudimos enviar el correo. Inténtalo de nuevo más tarde.')
        elif not (allowed_by_email and allowed_by_ip):
            messages.info(request, 'Espera un momento antes de solicitar otro código. Si la cuenta existe, enviaremos las instrucciones.')

        return redirect('password_reset_done')
    return render(request, 'usuarios/password_reset/password_reset_form.html', {'form': form})


@never_cache
def password_reset_done(request):
    return render(request, 'usuarios/password_reset/password_reset_done.html', {
        'form': PasswordResetCodeForm(),
    })


@never_cache
def password_reset_verify(request):
    form = PasswordResetCodeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        challenge_id = request.session.get(PASSWORD_RESET_CHALLENGE_SESSION_KEY)
        valid = False
        if challenge_id:
            with transaction.atomic():
                challenge = OtpChallenge.objects.select_for_update().filter(pk=challenge_id).first()
                if (challenge and challenge.consumed_at is None
                        and challenge.expires_at > timezone.now()
                        and challenge.attempts < PASSWORD_RESET_CODE_MAX_ATTEMPTS):
                    user_count = User.objects.filter(
                        email__iexact=challenge.email, is_active=True
                    ).count()
                    if user_count == 1 and check_password(form.cleaned_data['code'], challenge.pin_hash):
                        valid = True
                    else:
                        challenge.attempts += 1
                        fields = ['attempts']
                        if challenge.attempts >= PASSWORD_RESET_CODE_MAX_ATTEMPTS:
                            challenge.consumed_at = timezone.now()
                            fields.append('consumed_at')
                        challenge.save(update_fields=fields)

        if valid:
            request.session[PASSWORD_RESET_VERIFIED_SESSION_KEY] = challenge_id
            return redirect('password_reset_code_confirm')
        form.add_error('code', 'El código no es válido o venció. Solicita uno nuevo e inténtalo otra vez.')
    return render(request, 'usuarios/password_reset/password_reset_done.html', {
        'form': form,
    })


@never_cache
def password_reset_code_confirm(request):
    challenge_id = request.session.get(PASSWORD_RESET_CHALLENGE_SESSION_KEY)
    verified_id = request.session.get(PASSWORD_RESET_VERIFIED_SESSION_KEY)
    challenge = OtpChallenge.objects.filter(pk=challenge_id).first() if challenge_id else None
    if (not challenge or verified_id != challenge_id or challenge.consumed_at is not None
            or challenge.expires_at <= timezone.now()
            or challenge.attempts >= PASSWORD_RESET_CODE_MAX_ATTEMPTS):
        request.session.pop(PASSWORD_RESET_CHALLENGE_SESSION_KEY, None)
        request.session.pop(PASSWORD_RESET_VERIFIED_SESSION_KEY, None)
        return render(request, 'usuarios/password_reset/password_reset_confirm.html', {
            'validlink': False,
        })

    users = User.objects.filter(email__iexact=challenge.email, is_active=True)
    user = users.first() if users.count() == 1 else None
    if user is None:
        return render(request, 'usuarios/password_reset/password_reset_confirm.html', {
            'validlink': False,
        })

    form = SetPasswordForm(user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            locked_challenge = OtpChallenge.objects.select_for_update().filter(pk=challenge.pk).first()
            locked_user = User.objects.select_for_update().filter(pk=user.pk, is_active=True).first()
            if (not locked_challenge or not locked_user
                    or locked_challenge.consumed_at is not None
                    or locked_challenge.expires_at <= timezone.now()
                    or request.session.get(PASSWORD_RESET_VERIFIED_SESSION_KEY) != locked_challenge.pk):
                return render(request, 'usuarios/password_reset/password_reset_confirm.html', {
                    'validlink': False,
                })
            form.user = locked_user
            form.save()
            locked_challenge.consumed_at = timezone.now()
            locked_challenge.save(update_fields=['consumed_at'])
        request.session.pop(PASSWORD_RESET_CHALLENGE_SESSION_KEY, None)
        request.session.pop(PASSWORD_RESET_VERIFIED_SESSION_KEY, None)
        return redirect('password_reset_complete')

    return render(request, 'usuarios/password_reset/password_reset_confirm.html', {
        'validlink': True,
        'form': form,
    })

def _establish_password_session(request, user):
    login(request, user)
    request.session['tienda_desbloqueada'] = True
    request.session['vip_unlocked_email'] = user.email
    try:
        enviar_cupon_bienvenida(user, email=user.email)
    except Exception as exc:
        logger.error('Welcome email failed: exception=%s', type(exc).__name__)

def _safe_next(request, fallback='inicio'):
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return fallback

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    flash_messages = []
    seen_messages = set()
    for flash_message in messages.get_messages(request):
        message_text = str(flash_message).strip()
        if message_text and message_text not in seen_messages:
            seen_messages.add(message_text)
            flash_messages.append(flash_message)
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        _establish_password_session(request, user)
        messages.success(request, f'Bienvenido/a a SOLARY LUXURY, {user.first_name or user.username}.')
        return redirect(_safe_next(request, 'inicio'))
    return render(request, 'usuarios/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
        'login_messages': flash_messages,
    })

def registro_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _establish_password_session(request, user)
        messages.success(request, 'Tu cuenta se creó y quedó guardada. ¡Bienvenido/a a SOLARY LUXURY!')
        return redirect('inicio')
    return render(request, 'usuarios/registro.html', {'form': form})

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente de SOLARY LUXURY.")
    response = redirect('inicio')
    response.delete_cookie('sessionid')
    return response

@never_cache
@login_required(login_url='login')
def perfil_view(request):
    if request.user.is_staff or request.user.is_superuser:
        ordenes = PreOrden.objects.all().select_related('producto').order_by('-fecha_creacion')[:12]
        pedidos = Pedido.objects.all().select_related('producto').order_by('-fecha_creacion')[:12]
        trackers = Tracker.objects.all().select_related('pedido', 'preorden').order_by('-fecha_actualizacion')[:12]
    else:
        ordenes = PreOrden.objects.filter(
            usuario=request.user
        ).select_related('producto').order_by('-fecha_creacion')

        pedidos = Pedido.objects.filter(
            usuario=request.user
        ).select_related('producto').order_by('-fecha_creacion')

        trackers = Tracker.objects.filter(
            usuario=request.user
        ).select_related('pedido', 'preorden').order_by('-fecha_actualizacion')

    context = {
        'usuario': request.user,
        'ordenes': ordenes,
        'pedidos': pedidos,
        'trackers': trackers,
        'total_ordenes': ordenes.count(),
        'total_pedidos': pedidos.count(),
        'total_trackers': trackers.count(),
    }
    return render(request, 'usuarios/perfil.html', context)

def crear_ticket_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    contacto_alternativo = data.get('contacto_alternativo', '').strip()
    motivo = data.get('motivo', '').strip()
    mensaje = data.get('mensaje', '').strip()

    if not nombre:
        return JsonResponse({'success': False, 'error': 'Por favor ingresa tu nombre completo.'}, status=400)
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'success': False, 'error': 'Por favor ingresa un correo de cuenta válido.'}, status=400)
    if len(nombre) > 150 or len(email) > 254 or len(contacto_alternativo) > 150 or len(motivo) > 255 or len(mensaje) > 10000:
        return JsonResponse({'success': False, 'error': 'El mensaje excede el largo permitido.'}, status=400)
    if not mensaje:
        return JsonResponse({'success': False, 'error': 'Por favor detalla tu problema o solicitud.'}, status=400)

    codigo = f"SL-TK-{random.randint(10000, 99999)}"
    while TicketSoporte.objects.filter(codigo=codigo).exists():
        codigo = f"SL-TK-{random.randint(10000, 99999)}"

    ticket = TicketSoporte.objects.create(
        codigo=codigo,
        nombre=nombre,
        email=email,
        contacto_alternativo=contacto_alternativo,
        motivo=motivo or 'Sin acceso al correo de autenticación',
        mensaje=mensaje
    )

    return JsonResponse({
        'success': True,
        'ticket_id': ticket.codigo,
        'nombre': ticket.nombre,
        'email': ticket.email,
        'message': f'Ticket {ticket.codigo} registrado exitosamente. Nuestro equipo de Concierge te contactará a la brevedad.'
    })

EMAIL_TEMPLATES_CONFIG = {
    'preparando_pedido': {
        'nombre': '01 — Estamos Preparando tu Pedido',
        'template': 'emails/email_preparando_pedido.html',
        'asunto': 'SOLARY — Estamos preparando tu pedido SL-892104',
        'contexto': {
            'cliente_nombre': 'Test Test',
            'pedido_id': 'SL-892104',
            'fecha_estimada': 'Viernes, 3 de oct. – Lunes, 6 de oct.',
            'total_precio': '$244.990 CLP',
            'subtotal': '$205.874 CLP',
            'iva': '$39.116 CLP',
            'direccion': 'Av. Nueva Costanera 4020, Depto 601',
            'comuna': 'Vitacura, Región Metropolitana',
            'tracking_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/locales/informacion/?codigo=SL-892104',
            'items': [
                {
                    'nombre': 'Nike Air Force 1 Low × Syna World',
                    'subtitulo': 'Central Cee Special Edition · Black / Optic Yellow',
                    'talla': '9.5 US / 42.5 EU',
                    'codigo_estilo': 'FZ4210-001',
                    'cantidad': 1,
                    'precio_formateado': '$189.990 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
                },
            ],
            'orden': {
                'codigo_orden': 'SL-892104',
                'fecha_estimada': 'Viernes, 3 de oct. – Lunes, 6 de oct.',
                'nombre_cliente': 'Test Test',
                'subtotal': '$205.874 CLP',
                'iva': '$39.116 CLP',
                'total': '$244.990 CLP',
                'precio_formateado': '$244.990 CLP',
                'direccion': 'Av. Nueva Costanera 4020, Depto 601',
                'ciudad': 'Vitacura, Región Metropolitana',
                'metodo_pago': 'Apple Pay (Mastercard •••• 4242)',
            },
            'producto': {
                'nombre': 'Nike Air Force 1 Low × Syna World',
                'subtitulo': 'Central Cee Special Edition · Black / Optic Yellow',
                'codigo_estilo': 'FZ4210-001',
                'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
            }
        }
    },
    'pedido_despachado': {
        'nombre': '02 — Pedido Despachado (En Camino)',
        'template': 'emails/email_pedido_despachado.html',
        'asunto': 'SOLARY — Tu pedido está en camino (Guía DHL 9942019482)',
        'contexto': {
            'cliente_nombre': 'Test Test',
            'guia_dhl': '9942019482',
            'llegada_programada': 'Viernes, 3 de octubre de 2026',
            'transportista': 'DHL Express Worldwide',
            'total_precio': '$295.000 CLP',
            'estado_guia': 'En tránsito aéreo',
            'direccion': 'Av. Nueva Costanera 4020, Depto 601',
            'comuna': 'Vitacura, Santiago',
            'dhl_url': 'https://www.dhl.com/cl-es/home/tracking.html?tracking-id=9942019482',
            'items': [
                {
                    'nombre': 'Nike Sportswear Tech Fleece × Central Cee',
                    'subtitulo': 'Full-Zip Hoodie · Black / Metallic Edition',
                    'talla': 'L (Corte Boxy Europeo)',
                    'codigo_estilo': 'SL-TECH-CC-09',
                    'cantidad': 1,
                    'precio_formateado': '$240.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/tech_fleece_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
                }
            ],
            'orden': {
                'dhl_tracking': '9942019482',
                'fecha_entrega': 'Viernes, 3 de octubre de 2026',
                'nombre_cliente': 'Test Test',
                'total': '$295.000 CLP',
                'direccion': 'Av. Nueva Costanera 4020, Depto 601',
                'ciudad': 'Vitacura, Santiago',
            },
            'producto': {
                'nombre': 'Nike Sportswear Tech Fleece × Central Cee',
                'subtitulo': 'Full-Zip Hoodie · Black / Metallic Edition',
                'codigo_estilo': 'SL-TECH-CC-09',
                'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/tech_fleece_email.png',
            }
        }
    },
    'pedido_entregado': {
        'nombre': '03 — Pedido Entregado con Éxito',
        'template': 'emails/email_pedido_entregado.html',
        'asunto': 'SOLARY — Tu pedido ha sido entregado',
        'contexto': {
            'cliente_nombre': 'Test Test',
            'hora_entrega': '14:32 hrs en conserjería',
            'total_precio': '$244.990 CLP',
            'direccion': 'Av. Nueva Costanera 4020, Depto 601',
            'comuna': 'Vitacura, Santiago',
            'detalles_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/locales/informacion/?codigo=SL-892104',
            'items': [
                {
                    'nombre': 'Nike Air Force 1 Low × Syna World',
                    'subtitulo': 'Central Cee Special Edition · Black / Optic Yellow',
                    'talla': '9.5 US / 42.5 EU',
                    'codigo_estilo': 'FZ4210-001',
                    'cantidad': 1,
                    'precio_formateado': '$189.990 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
                },
            ],
            'orden': {
                'nombre_cliente': 'Test Test',
                'total': '$244.990 CLP',
                'direccion': 'Av. Nueva Costanera 4020, Depto 601',
            },
            'entrega': {
                'hora': '14:32 hrs',
                'lugar': 'conserjería',
                'firmado_por': 'Conserje de Turno',
                'detalles_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/locales/informacion/?codigo=SL-892104',
            },
            'producto': {
                'nombre': 'Syna World OG Skull Beanie',
                'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                'imagen_url': 'https://raw.githubusercontent.com/flyybnjj/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
            }
        }
    },
    'recibo_compra': {
        'nombre': '04 — Recibo Oficial de Compra',
        'template': 'emails/email_recibo_oficial_compra.html',
        'asunto': 'SOLARY LUXURY — Recibo fiscal oficial N.° 892104',
        'contexto': {
            'cliente_nombre': 'Test Test',
            'numero_recibo': '892104',
            'fecha_recibo': '27 de septiembre de 2026',
            'items': [
                {
                    'nombre': 'Nike Air Force 1 Low × Syna Central Cee',
                    'talla': '9.5 US',
                    'codigo_estilo': 'SL-AF1-042',
                    'cantidad': 1,
                    'precio_formateado': '$189.990 CLP',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'talla': 'Única',
                    'codigo_estilo': 'Black Edition',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                }
            ],
            'subtotal_neto': '$205.874 CLP',
            'iva_monto': '$39.116 CLP',
            'total_cancelado': '$244.990 CLP',
            'rut': '18.492.102-K',
            'comuna': 'Vitacura, Santiago',
            'factura_pdf_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/locales/informacion/?codigo=SL-892104',
            'factura': {
                'numero': '892104',
                'fecha': '27 de septiembre de 2026',
                'pdf_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/locales/informacion/?codigo=SL-892104',
            },
            'orden': {
                'nombre_cliente': 'Test Test',
                'rut': '18.492.102-K',
            }
        }
    },
    'cupon_bienvenida': {
        'nombre': '06 — Cupón de Bienvenida 15% OFF',
        'template': 'emails/email_cupon_bienvenida.html',
        'asunto': 'SOLARY — Bienvenido a Solary Archive: Tu beneficio 15% OFF (SOLARY-8K92F)',
        'contexto': {
            'cliente_nombre': 'Test Test',
            'cupon_codigo': 'SOLARY-8K92F',
            'vigencia_dias': '30 días',
            'tienda_url': 'http://ec2-32-193-109-160.compute-1.amazonaws.com/',
        }
    }
}

@user_passes_test(lambda user: user.is_staff or user.is_superuser, login_url='login')
def email_preview_view(request, plantilla='preparando_pedido'):
    if plantilla not in EMAIL_TEMPLATES_CONFIG:
        plantilla = 'preparando_pedido'

    config = EMAIL_TEMPLATES_CONFIG[plantilla]
    html_rendered = render_to_string(config['template'], config['contexto'])

    if request.GET.get('raw') == '1':
        from django.http import HttpResponse
        return HttpResponse(html_rendered, content_type='text/html; charset=utf-8')

    context = {
        'plantilla_actual': plantilla,
        'config_actual': config,
        'templates_list': EMAIL_TEMPLATES_CONFIG,
    }
    return render(request, 'usuarios/preview_emails_dashboard.html', context)
