import logging
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)

ALLOWED_EMAILS = {'avalosb758@gmail.com'}

class WhitelistEmailBackend(EmailBackend):
    """
    Backend de correo de seguridad para desarrollo y producción local.
    Garantiza de forma estricta e inviolable que NUNCA se envíe ningún correo
    a una dirección distinta de avalosb758@gmail.com.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        allowed_messages = []
        for msg in email_messages:
            original_to = list(msg.to)
            # Filtrar destinatarios principales
            msg.to = [addr for addr in msg.to if addr.strip().lower() in ALLOWED_EMAILS]
            
            # Filtrar CC y BCC si existen
            if hasattr(msg, 'cc') and msg.cc:
                msg.cc = [addr for addr in msg.cc if addr.strip().lower() in ALLOWED_EMAILS]
            if hasattr(msg, 'bcc') and msg.bcc:
                msg.bcc = [addr for addr in msg.bcc if addr.strip().lower() in ALLOWED_EMAILS]

            if msg.to or getattr(msg, 'cc', None) or getattr(msg, 'bcc', None):
                allowed_messages.append(msg)
            else:
                print(f"[EMAIL SECURITY GUARD] Envío bloqueado hacia {original_to}. REGLA ESTRICTA: Solo permitido avalosb758@gmail.com")

        if not allowed_messages:
            return 0

        return super().send_messages(allowed_messages)
