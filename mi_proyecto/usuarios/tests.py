import json
from django.test import TestCase, Client
from django.core import mail

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
        self.cliente.access_pin = "765432"
        self.cliente.pin_expires_at = timezone.now() + timedelta(minutes=10)
        self.cliente.save()

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
        self.assertIn("bloqueado", resp5.json().get('error', '').lower())

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
        user.cliente.access_pin = "112233"
        user.cliente.pin_expires_at = timezone.now() + timedelta(minutes=10)
        user.cliente.save()

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



