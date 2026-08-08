from django.contrib.auth import login
from django.core import signing
from django.core.mail import send_mail
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
    verify_url = request.build_absolute_uri(reverse('verify_email', args=[token]))
    body = render_to_string('emails/verification_email.txt', {'verify_url': verify_url})
    send_mail('Potwierdź adres email — NaukaAI', body, None, [user.email])


class RegisterView(CreateView):
    form_class = EmailRegistrationForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        existing = CustomUser.objects.filter(email__iexact=email).first()
        if existing is not None:
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
        else:
            user = form.save()
            _send_verification_email(user, self.request)
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
