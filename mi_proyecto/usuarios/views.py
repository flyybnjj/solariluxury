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

logger = logging.getLogger(__name__)


def generar_pin_otp():
    """Genera un PIN numérico de 6 dígitos criptográficamente seguro."""
    return f"{secrets.randbelow(900000) + 100000}"


def solicitar_acceso_view(request):
    """
    Paso 1 del Passwordless Login:
    - Cliente ingresa su correo electrónico.
    - Si el usuario no existe, se auto-crea la cuenta de cliente al instante (get_or_create).
    - Se genera un PIN de 6 dígitos con expiración de 10 minutos (timezone.now() + timedelta(minutes=10)).
    - Se envía el correo usando send_mail y la plantilla HTML de SOLARI LUXURY.
    - Se captura cualquier excepción SMTP con try-except y registro en consola para pruebas locales.
    - Se redirige a la pantalla de validación.
    """
    if request.user.is_authenticated:
        return redirect('inicio')

    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if next_url:
        request.session['auth_otp_next'] = next_url

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email or '@' not in email:
            messages.error(request, "Por favor introduce un correo electrónico válido.")
            return render(request, 'usuarios/solicitar_acceso.html', {'email': email, 'next_url': next_url})

        # Buscar usuario o auto-crearlo al instante
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            base_username = email.split('@')[0].replace('.', '_').replace('-', '_')
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email
            )
            user.set_unusable_password()
            user.save()

        # Obtener o crear perfil de cliente asociado
        cliente, _ = Cliente.objects.get_or_create(user=user)

        # Generar PIN aleatorio de 6 dígitos con expiración a 10 minutos
        pin = generar_pin_otp()
        cliente.access_pin = pin
        cliente.pin_expires_at = timezone.now() + timedelta(minutes=10)
        cliente.save()

        # Guardar correo en la sesión para el paso de validación
        request.session['auth_otp_email'] = email

        pin_spaced = f"{pin[:3]}   {pin[3:]}"
        cliente_nombre = user.get_full_name() or user.first_name or "Test Test"
        subject = f"SOLARY ID — Tu código de verificación: {pin}"
        html_message = render_to_string('usuarios/email_pin_acceso.html', {
            'pin': pin,
            'pin_spaced': pin_spaced,
            'cliente_nombre': cliente_nombre,
            'user': user,
            'email': email,
        })
        plain_message = (
            f"SOLARY ID — CÓDIGO DE VERIFICACIÓN\n\n"
            f"Tu código de verificación de Solary es: {pin}\n"
            f"Vigencia: 10 minutos.\n\n"
            f"Si tú no solicitaste este código, puedes ignorar este mensaje."
        )

        # Envío con try-except para evitar errores 500 y dejar registro en consola
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f"Hemos enviado un código PIN de 6 dígitos a {email}. Revisa tu correo.")
        except Exception as e:
            logger.error(f"[ERROR SMTP GMAIL] No se pudo conectar al servidor de correo: {e}")
            print("\n" + "="*70)
            print("  [SOLARI LUXURY - OTP LOCAL CONSOLE LOG]")
            print(f"  Destinatario: {email}")
            print(f"  PIN Generado: {pin}")
            print(f"  Expiracion  : {cliente.pin_expires_at} (10 minutos)")
            print(f"  Detalle SMTP: {e}")
            print("="*70 + "\n")
            messages.info(request, f"PIN generado para {email}. Si estas en pruebas locales, revisa la consola del servidor.")

        return redirect('validar_pin')

    return render(request, 'usuarios/solicitar_acceso.html', {'next_url': next_url})


def validar_pin_view(request):
    """
    Paso 2 del Passwordless Login:
    - Formulario para ingresar el PIN de 6 dígitos (con opción de reenvío si caducó).
    - Valida coincidencia y que el tiempo no haya superado pin_expires_at.
    - Si es correcto: inicia sesión con login(request, user), invalida el PIN (access_pin = None)
      y redirige al catálogo o bolsa de compras.
    """
    if request.user.is_authenticated:
        return redirect('inicio')

    email = request.session.get('auth_otp_email') or request.GET.get('email') or request.POST.get('email')
    if not email:
        messages.warning(request, "Por favor ingresa tu correo para recibir tu código PIN de acceso.")
        return redirect('solicitar_acceso')

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "No encontramos una cuenta asociada a este correo. Solicita un nuevo código.")
        return redirect('solicitar_acceso')

    cliente = getattr(user, 'cliente', None)
    if not cliente:
        messages.warning(request, "Perfil de cliente no encontrado. Solicita un nuevo código.")
        return redirect('solicitar_acceso')

    if cliente.esta_bloqueado():
        messages.error(request, "Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente por 15 minutos.")
        return render(request, 'usuarios/validar_pin.html', {
            'email': email,
            'pin_expirado': True,
            'segundos_restantes': 0,
        })

    if not cliente.access_pin or not cliente.pin_expires_at:
        messages.warning(request, "No hay ningún PIN activo o el código ya fue utilizado. Solicita uno nuevo.")
        return redirect('solicitar_acceso')

    if request.method == 'POST':
        pin_ingresado = request.POST.get('pin', '').strip()

        # Validación 1: Tiempo no haya superado pin_expires_at (10 minutos)
        if timezone.now() > cliente.pin_expires_at:
            cliente.clear_pin()
            messages.error(request, "El código PIN ha caducado (validez de 10 minutos). Haz clic en Reenviar para obtener uno nuevo.")
            return render(request, 'usuarios/validar_pin.html', {
                'email': email,
                'pin_expirado': True,
                'segundos_restantes': 0,
            })

        # Validación 2: Coincidencia del PIN con secrets.compare_digest
        if not secrets.compare_digest(str(cliente.access_pin).strip(), str(pin_ingresado).strip()):
            cliente.intentos_fallidos += 1
            if cliente.intentos_fallidos >= 5:
                cliente.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                cliente.clear_pin()
                cliente.save()
                messages.error(request, "Has superado el límite de 5 intentos fallidos. Tu acceso ha sido bloqueado por 15 minutos y el código PIN ha sido invalidado.")
                return render(request, 'usuarios/validar_pin.html', {
                    'email': email,
                    'pin_expirado': True,
                    'segundos_restantes': 0,
                })
            cliente.save()
            messages.error(request, f"El código PIN ingresado es incorrecto. Te quedan {5 - cliente.intentos_fallidos} intentos.")
            return render(request, 'usuarios/validar_pin.html', {
                'email': email,
                'pin_invalido': True,
                'segundos_restantes': max(0, int((cliente.pin_expires_at - timezone.now()).total_seconds())),
            })

        # 1. Resetear intentos y quemar el PIN inmediatamente
        cliente.intentos_fallidos = 0
        cliente.bloqueado_hasta = None
        cliente.clear_pin()
        user.access_pin = None
        user.pin_expires_at = None
        user.save()

        # 2. Iniciar sesión de usuario y fijar flags de acceso VIP (BUG-011)
        login(request, user)
        request.session['tienda_desbloqueada'] = True
        request.session['vip_unlocked_email'] = email

        # Enviar cupón de bienvenida exclusivamente en el primer login
        try:
            enviar_cupon_bienvenida(user, email=email)
        except Exception as e:
            logger.error(f"[ERROR CUPON BIENVENIDA] {e}")

        # 3. Vincular permanentemente todos los Pedidos, PreOrdenes y Trackers de este email al usuario
        PreOrden.objects.filter(email_cliente__iexact=email, usuario__isnull=True).update(usuario=user)
        Pedido.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)
        Tracker.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)

        # Limpiar datos de sesión
        request.session.pop('auth_otp_email', None)
        next_url = request.session.pop('auth_otp_next', None) or request.GET.get('next') or request.POST.get('next') or 'lista_productos'

        messages.success(request, f"¡Acceso verificado! Bienvenido/a a SOLARY LUXURY, {user.first_name or user.username}.")
        return redirect(next_url)

    # Calcular segundos restantes para el temporizador de frontend
    segundos_restantes = 600
    if cliente and cliente.pin_expires_at:
        diff = (cliente.pin_expires_at - timezone.now()).total_seconds()
        segundos_restantes = max(0, int(diff))

    return render(request, 'usuarios/validar_pin.html', {
        'email': email,
        'segundos_restantes': segundos_restantes,
    })


def reenviar_pin_view(request):
    """
    Reenvía un nuevo PIN de 6 dígitos con expiración a 10 minutos.
    """
    email = request.session.get('auth_otp_email') or request.GET.get('email')
    if not email:
        messages.warning(request, "Introduce tu correo para solicitar un nuevo PIN.")
        return redirect('solicitar_acceso')

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "Cuenta no encontrada. Solicita acceso nuevamente.")
        return redirect('solicitar_acceso')

    cliente, _ = Cliente.objects.get_or_create(user=user)
    pin = generar_pin_otp()
    cliente.access_pin = pin
    cliente.pin_expires_at = timezone.now() + timedelta(minutes=10)
    cliente.save()

    pin_spaced = f"{pin[:3]}   {pin[3:]}"
    cliente_nombre = user.get_full_name() or user.first_name or "Test Test"
    subject = f"SOLARY ID — Tu nuevo código de verificación: {pin}"
    html_message = render_to_string('usuarios/email_pin_acceso.html', {
        'pin': pin,
        'pin_spaced': pin_spaced,
        'cliente_nombre': cliente_nombre,
        'user': user,
        'email': email,
    })
    plain_message = f"SOLARY ID — Tu nuevo código de verificación de Solary es: {pin} (vigencia de 10 minutos)."

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        messages.success(request, f"Se ha despachado un nuevo código PIN de 6 dígitos a {email}.")
    except Exception as e:
        logger.error(f"[ERROR REENVIAR PIN] {e}")
        print("\n" + "="*70)
        print("  [SOLARI LUXURY - OTP REENVIADO CONSOLE LOG]")
        print(f"  Destinatario: {email}")
        print(f"  Nuevo PIN   : {pin}")
        print(f"  Expiracion  : {cliente.pin_expires_at} (10 minutos)")
        print(f"  Detalle SMTP: {e}")
        print("="*70 + "\n")
        messages.info(request, f"Nuevo PIN generado para {email}. Revisa la consola en pruebas locales.")

    return redirect('validar_pin')


# ══════════════════════════════════════════════════════════════════
# VISTAS ADICIONALES (PERFIL, LOGOUT, LEGACY LOGIN)
# ══════════════════════════════════════════════════════════════════

def login_view(request):
    """
    Ruta de login principal: redirige al flujo Passwordless OTP de Solari Luxury,
    manteniendo soporte de formulario clásico si se solicita explícitamente con ?legacy=1.
    """
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
    """Redirige al flujo Passwordless que auto-crea la cuenta instantáneamente."""
    return redirect('solicitar_acceso')


def logout_view(request):
    """Cierra la sesión del usuario de forma inmediata y limpia cookies para mostrar siempre la pantalla de login."""
    logout(request)
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente de SOLARY LUXURY.")
    response = redirect('inicio')
    response.delete_cookie('sessionid')
    return response


@login_required(login_url='solicitar_acceso')
def perfil_view(request):
    """Panel VIP de cliente con historial permanente de pedidos, pre-órdenes y trackers."""
    # Asegurar vinculación permanente si aún no estuvieran vinculados
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
    """Crea un ticket de soporte para usuarios que no tienen acceso a su correo o PIN."""
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


# ══════════════════════════════════════════════════════════════════
# PREVISUALIZACIÓN Y DESPACHO DE PRUEBA DE CORREOS APPLE STYLE
# ══════════════════════════════════════════════════════════════════

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
            'tracking_url': 'http://127.0.0.1:8000/locales/informacion/?codigo=SL-892104',
            'items': [
                {
                    'nombre': 'Nike Air Force 1 Low × Syna World',
                    'subtitulo': 'Central Cee Special Edition · Black / Optic Yellow',
                    'talla': '9.5 US / 42.5 EU',
                    'codigo_estilo': 'FZ4210-001',
                    'cantidad': 1,
                    'precio_formateado': '$189.990 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
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
                'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
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
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/tech_fleece_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
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
                'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/tech_fleece_email.png',
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
            'detalles_url': 'http://127.0.0.1:8000/locales/informacion/?codigo=SL-892104',
            'items': [
                {
                    'nombre': 'Nike Air Force 1 Low × Syna World',
                    'subtitulo': 'Central Cee Special Edition · Black / Optic Yellow',
                    'talla': '9.5 US / 42.5 EU',
                    'codigo_estilo': 'FZ4210-001',
                    'cantidad': 1,
                    'precio_formateado': '$189.990 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png',
                },
                {
                    'nombre': 'Syna World OG Skull Beanie',
                    'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                    'talla': 'Única',
                    'codigo_estilo': 'SYNA-BN-01',
                    'cantidad': 1,
                    'precio_formateado': '$55.000 CLP',
                    'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
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
                'detalles_url': 'http://127.0.0.1:8000/locales/informacion/?codigo=SL-892104',
            },
            'producto': {
                'nombre': 'Syna World OG Skull Beanie',
                'subtitulo': 'Algodón Pesado Jacquard · Black / Neutral Edition',
                'imagen_url': 'https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png',
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
            'factura_pdf_url': 'http://127.0.0.1:8000/locales/informacion/?codigo=SL-892104',
            'factura': {
                'numero': '892104',
                'fecha': '27 de septiembre de 2026',
                'pdf_url': 'http://127.0.0.1:8000/locales/informacion/?codigo=SL-892104',
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
            'tienda_url': 'http://127.0.0.1:8000/',
        }
    }
}


def email_preview_view(request, plantilla='codigo_seguridad'):
    """Permite visualizar en vivo cualquiera de las 6 plantillas de correo Apple de SOLARY."""
    if plantilla not in EMAIL_TEMPLATES_CONFIG:
        plantilla = 'codigo_seguridad'

    config = EMAIL_TEMPLATES_CONFIG[plantilla]
    html_rendered = render_to_string(config['template'], config['contexto'])

    # Si se pide raw=1 se devuelve directamente el HTML renderizado (ideal para iframe)
    if request.GET.get('raw') == '1':
        from django.http import HttpResponse
        return HttpResponse(html_rendered, content_type='text/html; charset=utf-8')

    context = {
        'plantilla_actual': plantilla,
        'config_actual': config,
        'templates_list': EMAIL_TEMPLATES_CONFIG,
    }
    return render(request, 'usuarios/preview_emails_dashboard.html', context)
