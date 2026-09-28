import json
from django.test import TestCase, Client
from django.core import mail
from django.contrib.auth.hashers import make_password
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from usuarios.models import OtpChallenge

class Bug002OpenRelayTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_anonymous_test_email_endpoint_forbidden_or_not_found(self):
        """
        BUG-002: Un usuario anónimo no debe poder usar /api/enviar-email-prueba/
        para enviar spam por Gmail SMTP. Debe retornar 404 o 403 y no despachar correo.
        """
        payload = {
            "email": "spam_target@victim.com",
            "plantilla": "cupon_bienvenida"
        }
        response = self.client.post(
            '/api/enviar-email-prueba/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        # El endpoint debe dar 404 Not Found (o 403 Forbidden)
        self.assertIn(response.status_code, [403, 404])
        self.assertEqual(len(mail.outbox), 0)


class Bug008RateLimitingPinTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        self.user = User.objects.create_user(username="bruteforcer", email="brute@test.com", password="Password123!")
        self.cliente = self.user.cliente
        OtpChallenge.objects.create(email=self.user.email, pin_hash=make_password('765432'), expires_at=timezone.now() + timedelta(minutes=10))

    def test_brute_force_pin_is_blocked_after_failed_attempts(self):
        """
        BUG-008: Tras 5 intentos fallidos consecutivos de PIN, el sistema
        debe bloquear al usuario (retornando 429 Too Many Requests), quemar
        el PIN y rechazar intentos posteriores.
        """
        # 4 intentos fallidos
        for i in range(4):
            resp = self.client.post('/api/validar-key/', data=json.dumps({
                "email": self.user.email,
                "pin": "000000"
            }), content_type='application/json')
            self.assertEqual(resp.status_code, 400)

        # 5to intento fallido -> debe bloquear (429) y quemar el PIN
        resp5 = self.client.post('/api/validar-key/', data=json.dumps({
            "email": self.user.email,
            "pin": "000000"
        }), content_type='application/json')
        self.assertEqual(resp5.status_code, 429)
        self.assertIn("intentos", resp5.json().get('error', '').lower())

        # 6to intento (incluso con el PIN original correcto) debe responder 429
        resp6 = self.client.post('/api/validar-key/', data=json.dumps({
            "email": self.user.email,
            "pin": "765432"
        }), content_type='application/json')
        self.assertEqual(resp6.status_code, 429)


class Bug011SessionFlagsTest(TestCase):
    def test_validar_pin_sets_tienda_desbloqueada_in_session(self):
        """
        BUG-011: Tanto validar_key como validar_pin_view deben fijar
        'tienda_desbloqueada' = True y 'vip_unlocked_email' en la sesión.
        """
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        user = User.objects.create_user(username="vipuser", email="vip@solary.cl", password="Password123!")
        OtpChallenge.objects.create(email=user.email, pin_hash=make_password('112233'), expires_at=timezone.now() + timedelta(minutes=10))

        # Simulamos sesión previa del paso 1
        s = self.client.session
        s['auth_otp_email'] = user.email
        s.save()

        from django.urls import reverse
        resp = self.client.post(reverse('validar_pin'), data={'pin': '112233'})
        self.assertEqual(resp.status_code, 302)
        # Verificar variables de sesión
        self.assertTrue(self.client.session.get('tienda_desbloqueada'))
        self.assertEqual(self.client.session.get('vip_unlocked_email'), user.email)


class Bug010BrandOrthographyTest(TestCase):
    def test_brand_spelling_in_validar_pin_and_logout(self):
        """
        BUG-010: La ortografía oficial de la marca es 'SOLARY' / 'SOLARY LUXURY',
        no 'Solari Luxury' ni 'Solari ID' en los formularios y mensajes.
        """
        # 1. Template validar_pin
        resp = self.client.get('/validar-pin/?email=test@brand.cl')
        # Renderiza con warning si no hay PIN, pero podemos renderizar el template directamente
        from django.template.loader import render_to_string
        html = render_to_string('usuarios/validar_pin.html', {'email': 'test@brand.cl'})
        self.assertNotIn('alt="Solari Luxury"', html)
        self.assertNotIn('Solari ID', html)
        self.assertIn('alt="SOLARY LUXURY"', html)
        self.assertIn('SOLARY ID', html)

        # 2. Mensaje de logout
        resp_logout = self.client.get('/logout/', follow=True)
        messages_list = list(resp_logout.context['messages'])
        self.assertTrue(any("SOLARY LUXURY" in str(m) for m in messages_list))
        self.assertFalse(any("Solari Luxury" in str(m) for m in messages_list))





@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='SOLARY <no-reply@example.test>')
class OtpLoginFlowTests(TestCase):
    def issue_test_pin(self, email='new-customer@outlook.test', pin='123456', expires=None):
        return OtpChallenge.objects.create(
            email=email, pin_hash=make_password(pin),
            expires_at=expires or timezone.now() + timedelta(minutes=10),
        )

    def test_new_email_is_emailed_before_customer_account_is_created(self):
        from django.urls import reverse
        response = self.client.post(reverse('solicitar_acceso'), {'email': 'new-customer@outlook.test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(__import__('django.contrib.auth.models', fromlist=['User']).User.objects.filter(email='new-customer@outlook.test').exists())
        challenge = OtpChallenge.objects.get(email='new-customer@outlook.test')
        from django.contrib.auth.hashers import check_password
        self.assertFalse(check_password('123456', challenge.pin_hash))

    def test_delivery_failure_does_not_claim_success_or_leave_valid_pin(self):
        from unittest.mock import patch
        from smtplib import SMTPRecipientsRefused
        from django.urls import reverse
        with patch('usuarios.otp.send_mail', side_effect=SMTPRecipientsRefused({'private@example.test': (554, b'MessageRejected')})):
            response = self.client.post(reverse('solicitar_acceso'), {'email': 'private@example.test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No pudimos enviar el correo')
        self.assertNotContains(response, 'Hemos enviado un código')
        self.assertIsNotNone(OtpChallenge.objects.get(email='private@example.test').consumed_at)

    def test_existing_customer_can_request_code(self):
        from django.contrib.auth.models import User
        from django.urls import reverse
        User.objects.create_user(username='old-customer', email='old-customer@example.test')
        response = self.client.post(reverse('solicitar_acceso'), {'email': 'old-customer@example.test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(OtpChallenge.objects.get(email='old-customer@example.test').attempts, 0)

    def test_valid_pin_logs_in_and_is_one_time(self):
        email = 'new-customer@outlook.test'
        self.issue_test_pin(email)
        session = self.client.session
        session['auth_otp_email'] = email
        session.save()
        response = self.client.post('/validar-pin/', {'pin': '123456'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id'))
        challenge = OtpChallenge.objects.get(email=email)
        self.assertIsNotNone(challenge.consumed_at)

    def test_expired_pin_is_rejected(self):
        email = 'expired@example.test'
        self.issue_test_pin(email, expires=timezone.now() - timedelta(seconds=1))
        from usuarios.otp import verify_otp
        valid, _, _ = verify_otp(email, '123456')
        self.assertFalse(valid)

    def test_reused_pin_is_rejected(self):
        email = 'reuse@example.test'
        self.issue_test_pin(email)
        from usuarios.otp import verify_otp
        self.assertTrue(verify_otp(email, '123456')[0])
        self.assertFalse(verify_otp(email, '123456')[0])

    def test_fifth_wrong_attempt_consumes_challenge(self):
        email = 'tries@example.test'
        self.issue_test_pin(email)
        from usuarios.otp import verify_otp
        for _ in range(4):
            valid, remaining, _ = verify_otp(email, '000000')
            self.assertFalse(valid)
        self.assertEqual(remaining, 1)
        valid, remaining, _ = verify_otp(email, '000000')
        self.assertFalse(valid)
        self.assertEqual(remaining, 0)
        self.assertIsNotNone(OtpChallenge.objects.get(email=email).consumed_at)

    def test_requests_are_limited_for_email_and_ip(self):
        from usuarios.otp import issue_otp, OtpRateLimited
        email = 'rate@example.test'
        issue_otp(email, '192.0.2.10')
        with self.assertRaises(OtpRateLimited):
            issue_otp(email, '192.0.2.10')
