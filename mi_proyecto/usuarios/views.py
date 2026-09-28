import logging
import random
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
import json
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone

from django.db import models
from catalogo.models import PreOrden, Pedido, Tracker
from .models import Cliente, TicketSoporte
from .forms import LoginForm
from .utils import enviar_cupon_bienvenida
from .otp import OtpDeliveryError, OtpRateLimited, issue_otp, verify_otp, complete_login

logger = logging.getLogger(__name__)

def generar_pin_otp():
    return f"{secrets.randbelow(1_000_000):06d}"

def _otp_ip(request):
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')

def solicitar_acceso_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if next_url:
        request.session['auth_otp_next'] = next_url
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().casefold()
        try:
            from django.core.validators import validate_email
            validate_email(email)
            issue_otp(email, _otp_ip(request))
        except OtpRateLimited:
            messages.error(request, 'Espera un minuto antes de solicitar otro código.')
            return render(request, 'usuarios/solicitar_acceso.html', {'email': email, 'next_url': next_url})
        except Exception as exc:
            if isinstance(exc, OtpDeliveryError):
                messages.error(request, 'No pudimos enviar el correo. Inténtalo de nuevo más tarde.')
            else:
                from django.core.exceptions import ValidationError
                if isinstance(exc, ValidationError):
                    messages.error(request, 'Por favor introduce un correo electrónico válido.')
                else:
                    logger.error('OTP request failed: exception=%s', type(exc).__name__)
                    messages.error(request, 'No pudimos enviar el correo. Inténtalo de nuevo más tarde.')
            return render(request, 'usuarios/solicitar_acceso.html', {'email': email, 'next_url': next_url})
        request.session['auth_otp_email'] = email
        messages.success(request, 'Si el correo puede recibir mensajes, enviaremos un código de acceso válido por 10 minutos.')
        return redirect('validar_pin')
    return render(request, 'usuarios/solicitar_acceso.html', {'next_url': next_url})

def validar_pin_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    email = request.session.get('auth_otp_email') or request.GET.get('email') or request.POST.get('email')
    if not email:
        messages.warning(request, 'Ingresa tu correo para solicitar un código de acceso.')
        return redirect('solicitar_acceso')
    email = email.strip().casefold()
    if request.method == 'POST':
        valid, remaining, user = verify_otp(email, request.POST.get('pin', '').strip())
        if not valid:
            messages.error(request, 'El código no es válido, venció o alcanzó el límite de intentos. Solicita uno nuevo.' if remaining == 0 else f'Código incorrecto. Te quedan {remaining} intentos.')
            return render(request, 'usuarios/validar_pin.html', {'email': email, 'pin_invalido': True, 'pin_expirado': remaining == 0, 'segundos_restantes': 0})
        complete_login(request, email, user)
        request.session.pop('auth_otp_email', None)
        next_url = request.session.pop('auth_otp_next', None) or request.GET.get('next') or request.POST.get('next') or 'lista_productos'
        messages.success(request, f'¡Acceso verificado! Bienvenido/a a SOLARY LUXURY, {user.first_name or user.username}.')
        return redirect(next_url)
    return render(request, 'usuarios/validar_pin.html', {'email': email, 'segundos_restantes': 600})

def reenviar_pin_view(request):
    if request.method != 'POST':
        return redirect('validar_pin')
    email = request.session.get('auth_otp_email')
    if not email:
        return redirect('solicitar_acceso')
    try:
        issue_otp(email, _otp_ip(request))
    except OtpRateLimited:
        messages.error(request, 'Espera un minuto antes de solicitar otro código.')
    except Exception as exc:
        logger.error('OTP resend failed: exception=%s', type(exc).__name__)
        messages.error(request, 'No pudimos enviar el correo. Inténtalo de nuevo más tarde.')
    else:
        messages.success(request, 'Si el correo puede recibir mensajes, enviaremos un nuevo código válido por 10 minutos.')
    return redirect('validar_pin')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.GET.get('legacy') != '1':
        return redirect('solicitar_acceso')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            try:
                enviar_cupon_bienvenida(user, email=user.email)
            except Exception as e:
                logger.error(f"[ERROR CUPON BIENVENIDA] {e}")
            messages.success(request, f"Bienvenido de nuevo, {user.username}.")
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'inicio')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})

def registro_view(request):
    return redirect('solicitar_acceso')

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente de SOLARY LUXURY.")
    response = redirect('inicio')
    response.delete_cookie('sessionid')
    return response

@login_required(login_url='solicitar_acceso')
def perfil_view(request):
    if request.user.email:
        PreOrden.objects.filter(email_cliente__iexact=request.user.email, usuario__isnull=True).update(usuario=request.user)
        Pedido.objects.filter(email__iexact=request.user.email, usuario__isnull=True).update(usuario=request.user)
        Tracker.objects.filter(email__iexact=request.user.email, usuario__isnull=True).update(usuario=request.user)

    if request.user.is_staff or request.user.is_superuser:
        ordenes = PreOrden.objects.all().select_related('producto').order_by('-fecha_creacion')[:12]
        pedidos = Pedido.objects.all().select_related('producto').order_by('-fecha_creacion')[:12]
        trackers = Tracker.objects.all().select_related('pedido', 'preorden').order_by('-fecha_actualizacion')[:12]
    else:
        ordenes = PreOrden.objects.filter(
            models.Q(usuario=request.user) | models.Q(email_cliente__iexact=request.user.email)
        ).select_related('producto').order_by('-fecha_creacion')

        pedidos = Pedido.objects.filter(
            models.Q(usuario=request.user) | models.Q(email__iexact=request.user.email)
        ).select_related('producto').order_by('-fecha_creacion')

        trackers = Tracker.objects.filter(
            models.Q(usuario=request.user) | models.Q(email__iexact=request.user.email)
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

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
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
    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'Por favor ingresa un correo de cuenta válido.'}, status=400)
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
    'codigo_seguridad': {
        'nombre': '05 — Código de Verificación (Solary ID)',
        'template': 'usuarios/email_pin_acceso.html',
        'asunto': 'Tu código de verificación de Solary: 482 910',
        'contexto': {
            'pin': '482910',
            'pin_spaced': '4 8 2   9 1 0',
            'cliente_nombre': 'Test Test',
            'user': {'first_name': 'Test', 'last_name': 'Test'},
        }
    },
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

def email_preview_view(request, plantilla='codigo_seguridad'):
    if plantilla not in EMAIL_TEMPLATES_CONFIG:
        plantilla = 'codigo_seguridad'

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
