from django import forms
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView
from django_ratelimit.decorators import ratelimit

from .forms import EmailRegistrationForm
from .models import CustomUser
from .tokens import make_verification_token, read_verification_token


def _send_verification_email(user, request):
    token = make_verification_token(user)
    verify_url = request.build_absolute_uri(reverse('accounts:verify_email', args=[token]))
    body = render_to_string('emails/verification_email.txt', {'verify_url': verify_url})
    send_mail('Potwierdź adres email — NaukaAI', body, None, [user.email])


class RegisterView(CreateView):
    form_class = EmailRegistrationForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = None
        existing = CustomUser.objects.filter(email__iexact=email).first()
        if existing is None:
            try:
                user = form.save()
            except IntegrityError:
                # Lost a race with a concurrent registration for the same
                # email between the check above and save() — fall through to
                # the "notify existing owner" path instead of a raw 500.
                existing = CustomUser.objects.filter(email__iexact=email).first()

        if user is not None:
            _send_verification_email(user, self.request)
        elif existing is not None:
            # Same generic response as a real signup — the existing owner gets notified
            # instead of the submitter, so this endpoint can't be used to enumerate
            # registered emails.
            send_mail(
                'Próba rejestracji na Twój adres email — NaukaAI',
                'Ktoś próbował założyć nowe konto NaukaAI na Twój adres email, ale masz już '
                'konto. Jeśli to nie Ty, możesz zignorować tę wiadomość.',
                None,
                [existing.email],
            )
        return render(self.request, 'registration/check_email.html')


def verify_email(request, token):
    try:
        pk = read_verification_token(token)
    except (signing.SignatureExpired, signing.BadSignature):
        return render(request, 'registration/verify_failed.html')

    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return render(request, 'registration/verify_failed.html')

    if user.is_active:
        # Already verified — the signed link stays valid for its full 24h
        # window, so a second click (or a leaked/replayed link) must not act
        # as a standing magic-login; only the first click auto-logs in.
        return redirect('login')

    user.is_active = True
    user.save(update_fields=['is_active'])
    login(request, user)
    return redirect('flashcards:topics')


@ratelimit(key='post:email', rate='1/m', block=True, method=['POST'])
def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        user = CustomUser.objects.filter(email__iexact=email, is_active=False).first()
        if user is not None:
            _send_verification_email(user, request)
        return render(request, 'registration/check_email.html')
    return redirect('login')


class CompleteEmailForm(forms.Form):
    email = forms.EmailField(label='Email')


@login_required
def complete_email(request):
    if request.user.email:
        return redirect('flashcards:topics')
    if request.method == 'POST':
        form = CompleteEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            verified_user = None
            existing = CustomUser.objects.filter(email__iexact=email).first()
            if existing is None:
                user = request.user
                # Only email changes here — is_active was already True for this
                # legacy account before this change shipped and must stay that way.
                user.email = email
                try:
                    user.save(update_fields=['email'])
                except IntegrityError:
                    # Lost a race with a concurrent claim on the same email —
                    # fall through to the "notify existing owner" path below.
                    user.email = None
                    existing = CustomUser.objects.filter(email__iexact=email).first()
                else:
                    verified_user = user

            if verified_user is not None:
                _send_verification_email(verified_user, request)
            elif existing is not None:
                # Same generic response as a successful submission — an
                # authenticated legacy user must not be able to use this form
                # to probe whether an arbitrary email is already registered
                # (same enumeration protection as RegisterView.form_valid).
                send_mail(
                    'Próba dodania Twojego adresu email — NaukaAI',
                    'Ktoś próbował dodać Twój adres email do innego konta NaukaAI. '
                    'Jeśli to nie Ty, możesz zignorować tę wiadomość.',
                    None,
                    [existing.email],
                )
            return render(request, 'registration/check_email.html')
    else:
        form = CompleteEmailForm()
    return render(request, 'registration/complete_email.html', {'form': form})
