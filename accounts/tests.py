import time
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomUser
from .tokens import VERIFICATION_MAX_AGE, make_verification_token


def _make_user(email, password='testpass123', is_active=False):
    user = CustomUser(email=email, is_active=is_active)
    user.set_password(password)
    user.save()
    return user


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class RegistrationTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_registration_creates_inactive_user_and_sends_one_email(self):
        response = self.client.post(reverse('register'), {
            'email': 'new@example.com',
            'password1': 'a-strong-passw0rd',
            'password2': 'a-strong-passw0rd',
        })
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(email='new@example.com')
        self.assertFalse(user.is_active)
        self.assertIsNone(user.username)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('new@example.com', mail.outbox[0].to)

    def test_duplicate_email_registration_creates_no_second_user_and_shows_generic_page(self):
        _make_user('existing@example.com')
        response = self.client.post(reverse('register'), {
            'email': 'existing@example.com',
            'password1': 'a-strong-passw0rd',
            'password2': 'a-strong-passw0rd',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/check_email.html')
        self.assertEqual(CustomUser.objects.filter(email='existing@example.com').count(), 1)
        # Notice goes to the existing owner, not a rejection to the submitter.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('existing@example.com', mail.outbox[0].to)


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class EmailVerificationTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_valid_token_activates_account_and_logs_in(self):
        user = _make_user('verify@example.com')
        token = make_verification_token(user)
        response = self.client.get(reverse('verify_email', args=[token]))
        self.assertRedirects(response, reverse('flashcards:topics'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_expired_token_rejected_with_resend_option(self):
        user = _make_user('expired@example.com')
        token = make_verification_token(user)
        future = time.time() + VERIFICATION_MAX_AGE + 3600
        with patch('django.core.signing.time.time', return_value=future):
            response = self.client.get(reverse('verify_email', args=[token]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/verify_failed.html')
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_tampered_token_rejected(self):
        user = _make_user('tampered@example.com')
        token = make_verification_token(user)
        tampered = token[:-1] + ('a' if token[-1] != 'a' else 'b')
        response = self.client.get(reverse('verify_email', args=[tampered]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/verify_failed.html')
        user.refresh_from_db()
        self.assertFalse(user.is_active)


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class ResendVerificationTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_resend_rate_limited_to_one_per_minute_per_email(self):
        _make_user('resend@example.com')
        first = self.client.post(reverse('resend_verification'), {'email': 'resend@example.com'})
        second = self.client.post(reverse('resend_verification'), {'email': 'resend@example.com'})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)


def _make_legacy_user(username, password='testpass123'):
    # Pre-existing (pre-change) account: no email, already active — the state
    # every real production user is in going into this change.
    user = CustomUser(username=username, email=None, is_active=True)
    user.set_password(password)
    user.save()
    return user


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class LoginTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_correct_email_and_password_login_succeeds_for_verified_account(self):
        _make_user('login@example.com', password='a-strong-passw0rd', is_active=True)
        response = self.client.post(reverse('login'), {
            'username': 'login@example.com',
            'password': 'a-strong-passw0rd',
        })
        self.assertTrue(self.client.session.get('_auth_user_id'))
        self.assertRedirects(response, '/flashcards/topics/')

    def test_wrong_email_or_password_show_identical_generic_error(self):
        _make_user('known@example.com', password='a-strong-passw0rd', is_active=True)
        wrong_password = self.client.post(reverse('login'), {
            'username': 'known@example.com',
            'password': 'wrong-password',
        })
        wrong_email = self.client.post(reverse('login'), {
            'username': 'unknown@example.com',
            'password': 'a-strong-passw0rd',
        })
        self.assertEqual(
            wrong_password.context['form'].errors['__all__'],
            wrong_email.context['form'].errors['__all__'],
        )

    def test_correct_credentials_for_unverified_account_show_distinct_message(self):
        _make_user('unverified@example.com', password='a-strong-passw0rd', is_active=False)
        response = self.client.post(reverse('login'), {
            'username': 'unverified@example.com',
            'password': 'a-strong-passw0rd',
        })
        self.assertIn('niezweryfikowane', str(response.context['form'].errors['__all__']))
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_legacy_account_logs_in_via_old_username(self):
        _make_legacy_user('legacyuser', password='a-strong-passw0rd')
        response = self.client.post(reverse('login'), {
            'username': 'legacyuser',
            'password': 'a-strong-passw0rd',
        })
        self.assertTrue(self.client.session.get('_auth_user_id'))
        # Login itself succeeds and redirects to LOGIN_REDIRECT_URL — the
        # further redirect to complete-email (no email on file) is the
        # RequireEmailMiddleware's job, covered separately below, not login's.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/flashcards/topics/')


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class LegacyAccountGateTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_legacy_account_redirected_to_complete_email_and_stays_active(self):
        _make_legacy_user('legacyuser2', password='a-strong-passw0rd')
        self.client.login(username='legacyuser2', password='a-strong-passw0rd')
        response = self.client.get(reverse('flashcards:topics'))
        self.assertRedirects(response, reverse('complete_email'))
        user = CustomUser.objects.get(username='legacyuser2')
        self.assertTrue(user.is_active)

    def test_legacy_account_can_still_reach_exempt_paths_without_looping(self):
        user = _make_legacy_user('legacyuser3', password='a-strong-passw0rd')
        self.client.login(username='legacyuser3', password='a-strong-passw0rd')
        response = self.client.get(reverse('complete_email'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('complete_email'), {'email': 'legacyuser3@example.com'})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, 'legacyuser3@example.com')
        self.assertTrue(user.is_active)
