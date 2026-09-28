import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def enviar_cupon_bienvenida(user, email=None):
    """
    Envía el correo de Cupón de Descuento de Bienvenida (15% OFF) al usuario
    exclusivamente en su primer inicio de sesión.
    Marca ha_recibido_cupon = True en la base de datos para garantizar que
    solo se envíe la primera vez.
    """
    from .models import Cliente

    if not user:
        return False

    cliente, _ = Cliente.objects.get_or_create(user=user)

    if cliente.ha_recibido_cupon:
        return False  # Ya lo recibió anteriormente

    # Marcar inmediatamente para prevenir condiciones de carrera
    cliente.ha_recibido_cupon = True
    cliente.save(update_fields=['ha_recibido_cupon'])

    destinatario = email or user.email
    if not destinatario:
        return False

    cliente_nombre = user.get_full_name() or user.first_name or ""
    if not cliente_nombre or cliente_nombre.lower() in ['test test', 'none', '']:
        cliente_nombre = destinatario.split('@')[0].replace('.', ' ').title()

    subject = "SOLARY — Bienvenido a Solary Archive: Tu beneficio 15% OFF"
    context = {
        'cliente_nombre': cliente_nombre,
        'user': user,
        'email': destinatario,
        'cupon_codigo': 'SOLARY15',
        'vigencia_dias': '30 días',
        'tienda_url': 'http://127.0.0.1:8000/',
    }

    html_message = render_to_string('emails/email_cupon_bienvenida.html', context)
    plain_message = (
        f"BIENVENIDO A SOLARY ARCHIVE\n\n"
        f"Hola {cliente_nombre},\n"
        f"Como beneficio exclusivo por activar tu SOLARY ID, tienes un 15% de descuento en tu primera compra.\n"
        f"Código de descuento: SOLARY15\n"
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
        logger.info(f"[SOLARY WELCOME EMAIL] Cupón enviado con éxito a {destinatario}")
        print(f"\n[OK] Cupón de bienvenida (15% OFF) enviado vía Gmail SMTP a {destinatario}\n")
        return True
    except Exception as e:
        logger.error(f"[ERROR SMTP CUPON BIENVENIDA] No se pudo enviar el correo a {destinatario}: {e}")
        print(f"\n[ERROR SMTP] Error al enviar cupón de bienvenida a {destinatario}: {e}\n")
        return False
