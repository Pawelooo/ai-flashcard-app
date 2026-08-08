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
