import logging
import random
import string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generar_codigo_cupon_unico(user=None):
    """
    Genera un código de cupón de descuento único y exclusivo para el usuario (ej: SOLARY-7K2X9).
    Evita colisiones verificando en la base de datos de Clientes.
    """
    from .models import Cliente
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    
    for _ in range(50):
        sufijo = ''.join(random.choices(chars, k=5))
        codigo = f"SOLARY-{sufijo}"
        if not Cliente.objects.filter(cupon_bienvenida_codigo=codigo).exists():
            return codigo
    return f"SOLARY-{random.randint(10000, 99999)}"


def enviar_cupon_bienvenida(user, email=None):
    """
    Envía el correo de Cupón de Descuento de Bienvenida (15% OFF) al usuario
    con un CÓDIGO ÚNICO Y PERSONALIZADO exclusivamente en su primer inicio de sesión.
    Marca ha_recibido_cupon = True y almacena cupon_bienvenida_codigo en la base de datos.
    """
    from .models import Cliente

    if not user:
        return False

    cliente, _ = Cliente.objects.get_or_create(user=user)

    if cliente.ha_recibido_cupon and cliente.cupon_bienvenida_codigo:
        return False  # Ya lo recibió anteriormente

    # Generar o recuperar código único para este cliente
    if not cliente.cupon_bienvenida_codigo:
        codigo_cupon = generar_codigo_cupon_unico(user)
        cliente.cupon_bienvenida_codigo = codigo_cupon
    else:
        codigo_cupon = cliente.cupon_bienvenida_codigo

    # Marcar inmediatamente para prevenir condiciones de carrera
    cliente.ha_recibido_cupon = True
    cliente.save(update_fields=['ha_recibido_cupon', 'cupon_bienvenida_codigo'])

    destinatario = email or user.email
    if not destinatario:
        return False

    cliente_nombre = user.get_full_name() or user.first_name or ""
    if not cliente_nombre or cliente_nombre.lower() in ['test test', 'none', '']:
        cliente_nombre = destinatario.split('@')[0].replace('.', ' ').title()

    subject = f"SOLARY — Bienvenido a Solary Archive: Tu beneficio 15% OFF ({codigo_cupon})"
    context = {
        'cliente_nombre': cliente_nombre,
        'user': user,
        'email': destinatario,
        'cupon_codigo': codigo_cupon,
        'vigencia_dias': '30 días',
        'tienda_url': 'http://127.0.0.1:8000/',
    }

    html_message = render_to_string('emails/email_cupon_bienvenida.html', context)
    plain_message = (
        f"BIENVENIDO A SOLARY ARCHIVE\n\n"
        f"Hola {cliente_nombre},\n"
        f"Como beneficio exclusivo por activar tu SOLARY ID, tienes un 15% de descuento personal e intransferible en tu primera compra.\n"
        f"Tu código de descuento único: {codigo_cupon}\n"
        f"Vigencia: 30 días.\n\n"
        f"Ingresa a la tienda oficial: http://127.0.0.1:8000/\n"
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"[SOLARY WELCOME EMAIL] Cupón único {codigo_cupon} enviado con éxito a {destinatario}")
        print(f"\n[OK] Cupón de bienvenida único ({codigo_cupon} - 15% OFF) enviado vía Gmail SMTP a {destinatario}\n")
        return True
    except Exception as e:
        logger.error(f"[ERROR SMTP CUPON BIENVENIDA] No se pudo enviar el correo a {destinatario}: {e}")
        print(f"\n[ERROR SMTP] Error al enviar cupón de bienvenida a {destinatario}: {e}\n")
        return False
