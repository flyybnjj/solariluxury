from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch


class TraditionalAccountFlowTests(TestCase):
    def test_password_recovery_uses_custom_styled_templates(self):
        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auth-card')
        self.assertContains(response, 'ENVIAR ENLACE')
        self.assertContains(response, 'class="guest-view"')
        self.assertContains(response, '.guest-view main { padding-top: 0; }')
        self.assertNotContains(response, 'Administración de Django')

    @patch('usuarios.views.enviar_cupon_bienvenida')
    def test_new_account_is_saved_with_hashed_password_and_authenticated(self, _send_welcome):
        response = self.client.post(reverse('registro'), {
            'username': 'new-customer',
            'email': 'new-customer@example.test',
            'password1': 'SafePassphrase-2026!x',
            'password2': 'SafePassphrase-2026!x',
        })

        self.assertRedirects(response, reverse('inicio'))
        user = User.objects.get(username='new-customer')
        self.assertEqual(user.email, 'new-customer@example.test')
        self.assertNotEqual(user.password, 'SafePassphrase-2026!x')
        self.assertTrue(user.check_password('SafePassphrase-2026!x'))
        self.assertTrue(user.cliente)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    @patch('usuarios.views.enviar_cupon_bienvenida')
    def test_existing_account_can_login_by_email(self, _send_welcome):
        user = User.objects.create_user(
            username='existing-customer', email='old@example.test', password='OldPassphrase-2026!x'
        )
        response = self.client.post(reverse('login'), {
            'username': 'OLD@example.test', 'password': 'OldPassphrase-2026!x'
        })

        self.assertRedirects(response, reverse('lista_productos'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_invalid_credentials_do_not_authenticate(self):
        User.objects.create_user(username='customer', email='customer@example.test', password='CorrectPass-2026!x')
        response = self.client.post(reverse('login'), {'username': 'customer', 'password': 'wrong'})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='accounts@example.test')
    def test_password_recovery_changes_database_password(self):
        user = User.objects.create_user(
            username='recover-me', email='recover@example.test', password='BeforeReset-2026!x'
        )
        response = self.client.post(reverse('password_reset'), {'email': user.email})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('SOLARY LUXURY', mail.outbox[0].subject)
        self.assertIn('restablecer-password', mail.outbox[0].body)
        reset_url = next(line for line in mail.outbox[0].body.splitlines() if '/restablecer-password/' in line)
        response = self.client.get(reset_url, follow=True)
        self.assertEqual(response.status_code, 200)
        uid, token = reset_url.rstrip('/').split('/')[-2:]
        response = self.client.post(response.request['PATH_INFO'], {
            'new_password1': 'AfterReset-2026!x', 'new_password2': 'AfterReset-2026!x'
        })

        self.assertRedirects(response, reverse('password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('AfterReset-2026!x'))
        self.assertFalse(user.check_password('BeforeReset-2026!x'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_recovery_response_is_generic_for_unknown_email(self):
        response = self.client.post(reverse('password_reset'), {'email': 'unknown@example.test'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_pin_routes_are_no_longer_available_for_authentication(self):
        response = self.client.post('/api/solicitar-key/', {'email': 'new@example.test'})
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('validar_pin'))
        self.assertRedirects(response, reverse('login'))
