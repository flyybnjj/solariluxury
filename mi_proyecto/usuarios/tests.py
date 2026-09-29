from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
import json


class SupportTicketSecurityTests(TestCase):
    def test_favicon_redirects_to_store_brand_asset(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/static/img/logo_marca.png')

    def test_ticket_requires_csrf_and_accepts_valid_contact_from_store_page(self):
        client = Client(enforce_csrf_checks=True)
        payload = json.dumps({
            'nombre': 'Cliente de prueba',
            'email': 'cliente@example.test',
            'mensaje': 'Consulta de prueba',
        })
        rejected = client.post('/api/crear-ticket/', payload, content_type='application/json')
        self.assertEqual(rejected.status_code, 403)

        page = client.get('/locales/')
        self.assertEqual(page.status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        accepted = client.post(
            '/api/crear-ticket/', payload, content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertTrue(accepted.json()['success'])

    def test_ticket_rejects_malformed_email(self):
        response = self.client.post('/api/crear-ticket/', {
            'nombre': 'Cliente', 'email': 'not-an-email', 'mensaje': 'Consulta',
        })
        self.assertEqual(response.status_code, 400)


class TraditionalAccountFlowTests(TestCase):
    def test_password_recovery_uses_custom_styled_templates(self):
        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auth-card')
        self.assertContains(response, 'ENVIAR ENLACE')
        self.assertContains(response, 'class="apple-dots-svg"')
        self.assertContains(response, '@keyframes appleDotsMotion')
        self.assertContains(response, 'class="guest-view"')
        self.assertContains(response, '.guest-view main { padding-top: 0; min-height: 100vh; background: #ebebf0; }')
        self.assertNotContains(response, 'class="sub-footer"')
        self.assertNotContains(response, 'Administración de Django')

    def test_registration_uses_the_same_animated_brand_mark_as_login(self):
        response = self.client.get(reverse('registro'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="apple-dots-svg"')
        self.assertContains(response, '@keyframes appleDotsMotion')

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
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.groups.count(), 0)
        self.assertEqual(user.user_permissions.count(), 0)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    @patch('usuarios.views.enviar_cupon_bienvenida')
    def test_existing_account_can_login_by_email(self, _send_welcome):
        user = User.objects.create_user(
            username='existing-customer', email='old@example.test', password='OldPassphrase-2026!x'
        )
        response = self.client.post(reverse('login'), {
            'username': 'OLD@example.test', 'password': 'OldPassphrase-2026!x'
        })

        self.assertRedirects(response, reverse('inicio'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        campaign_home = self.client.get(reverse('inicio'))
        self.assertContains(campaign_home, 'id="loader"')
        self.assertContains(campaign_home, 'setTimeout(dismissLoader, 1800)')
        self.assertContains(campaign_home, 'linear-gradient(90deg, #ff3b30 0%, #ff6a00 52%, #ff9f0a 100%)')

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

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='accounts@example.test')
    def test_active_legacy_account_without_password_can_set_one_from_email(self):
        user = User.objects.create_user(
            username='legacy-no-password', email='legacy-reset@example.test', password=None
        )
        self.assertFalse(user.has_usable_password())

        response = self.client.post(reverse('password_reset'), {'email': user.email})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(line for line in mail.outbox[0].body.splitlines() if '/restablecer-password/' in line)
        response = self.client.get(reset_url, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(response.request['PATH_INFO'], {
            'new_password1': 'FirstPassword-2026!x', 'new_password2': 'FirstPassword-2026!x'
        })

        self.assertRedirects(response, reverse('password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password('FirstPassword-2026!x'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_recovery_response_is_generic_for_unknown_email(self):
        response = self.client.post(reverse('password_reset'), {'email': 'unknown@example.test'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_inactive_account_does_not_receive_password_reset_email(self):
        user = User.objects.create_user(
            username='inactive-customer', email='inactive@example.test', password=None, is_active=False
        )
        response = self.client.post(reverse('password_reset'), {'email': user.email})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_pin_routes_are_no_longer_available_for_authentication(self):
        response = self.client.post('/api/solicitar-key/', {'email': 'new@example.test'})
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('validar_pin'))
        self.assertRedirects(response, reverse('login'))
