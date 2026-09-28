import hashlib
import hmac
import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import IntegrityError, transaction, models

from .models import Cliente, OtpChallenge, OtpRateLimit

logger = logging.getLogger(__name__)

def _safe_error_message(exc, pin=''):
    message = str(exc)
    for secret in (settings.EMAIL_HOST_PASSWORD, settings.EMAIL_HOST_USER, pin):
        if secret:
            message = message.replace(secret, '[REDACTED]')
    return re.sub(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", '[EMAIL]', message)[:300]

class OtpRateLimited(Exception):
    pass

class OtpDeliveryError(Exception):
    pass

def normalize_email(email):
    return (email or '').strip().casefold()

def _fingerprint(value):
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()

def _record_request(email, ip_address):
    now = timezone.now()
    subjects = [('email', _fingerprint('email:' + email))]
    if ip_address:
        subjects.append(('ip', _fingerprint('ip:' + ip_address)))
    with transaction.atomic():
        rows = []
        for kind, digest in subjects:
            try:
                row, _ = OtpRateLimit.objects.get_or_create(
                    kind=kind, subject_hash=digest,
                    defaults={'window_started_at': now, 'last_requested_at': now, 'requests_count': 0},
                )
            except IntegrityError:
                row = OtpRateLimit.objects.get(kind=kind, subject_hash=digest)
            rows.append(OtpRateLimit.objects.select_for_update().get(pk=row.pk))
        for row in rows:
            if now - row.window_started_at >= timedelta(hours=1):
                row.window_started_at = now
                row.requests_count = 0
            if row.requests_count >= 5 or (row.requests_count > 0 and now - row.last_requested_at < timedelta(seconds=60)):
                raise OtpRateLimited
        for row in rows:
            row.last_requested_at = now
            row.requests_count += 1
            row.save(update_fields=['window_started_at', 'last_requested_at', 'requests_count'])

def issue_otp(email, ip_address=''):
    email = normalize_email(email)
    try:
        from django.core.validators import validate_email
        validate_email(email)
    except ValidationError:
        raise
    _record_request(email, ip_address or '')
    now = timezone.now()
    OtpChallenge.objects.filter(email=email, consumed_at__isnull=True).update(consumed_at=now)
    pin = f'{secrets.randbelow(1_000_000):06d}'
    challenge = OtpChallenge.objects.create(
        email=email,
        pin_hash=make_password(pin),
        expires_at=now + timedelta(minutes=10),
    )
    try:
        count = send_mail(
            subject='SOLARY ID — Tu código de acceso',
            message=f'Tu código de acceso es {pin}. Vence en 10 minutos. Si no lo solicitaste, ignora este correo.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=render_to_string('usuarios/email_pin_simple.html', {'pin': pin}),
            fail_silently=False,
        )
        if count != 1:
            raise OtpDeliveryError('mail backend did not accept the message')
    except Exception as exc:
        challenge.consumed_at = timezone.now()
        challenge.save(update_fields=['consumed_at'])
        code = getattr(exc, 'smtp_code', None)
        logger.error('OTP email delivery failed: exception=%s smtp_code=%s detail=%s', type(exc).__name__, code, _safe_error_message(exc, pin))
        raise OtpDeliveryError from exc
    return challenge

def verify_otp(email, candidate):
    email = normalize_email(email)
    now = timezone.now()
    with transaction.atomic():
        challenge = OtpChallenge.objects.select_for_update().filter(
            email=email, consumed_at__isnull=True,
        ).order_by('-created_at').first()
        if not challenge or challenge.expires_at <= now:
            if challenge:
                challenge.consumed_at = now
                challenge.save(update_fields=['consumed_at'])
            return False, 0, None
        if not candidate or len(str(candidate)) != 6 or not str(candidate).isdigit() or not check_password(str(candidate), challenge.pin_hash):
            OtpChallenge.objects.filter(pk=challenge.pk, consumed_at__isnull=True).update(attempts=models.F('attempts') + 1)
            challenge.refresh_from_db(fields=['attempts', 'consumed_at'])
            remaining = max(0, 5 - challenge.attempts)
            if challenge.attempts >= 5:
                OtpChallenge.objects.filter(pk=challenge.pk, consumed_at__isnull=True).update(consumed_at=now)
            return False, remaining, None
        consumed = OtpChallenge.objects.filter(pk=challenge.pk, consumed_at__isnull=True).update(consumed_at=now)
        if not consumed:
            return False, 0, None
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            base = email.split('@', 1)[0].replace('.', '_').replace('-', '_')[:140] or 'cliente'
            username = base
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f'{base[:130]}_{suffix}'
                suffix += 1
            user = User.objects.create_user(username=username, email=email)
            user.set_unusable_password()
            user.save(update_fields=['password'])
        Cliente.objects.get_or_create(user=user)
        return True, 0, user

def complete_login(request, email, user):
    auth_login(request, user)
    request.session['tienda_desbloqueada'] = True
    request.session['vip_unlocked_email'] = email
    try:
        from .utils import enviar_cupon_bienvenida
        enviar_cupon_bienvenida(user, email=email)
    except Exception as exc:
        logger.error('Welcome email failed: exception=%s', type(exc).__name__)
    from catalogo.models import PreOrden, Pedido, Tracker
    PreOrden.objects.filter(email_cliente__iexact=email, usuario__isnull=True).update(usuario=user)
    Pedido.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)
    Tracker.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)
