from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class EmailRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email',)

    def validate_unique(self):
        # Skip ModelForm's automatic unique-email check — the view decides what happens
        # for an already-registered email (generic "check your email" response either
        # way, notice sent to the existing owner instead of the submitter) so a duplicate
        # must never surface here as a form field error (enumeration protection).
        pass

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        # CharField.get_default() returns '', not None, even though username is
        # null=True — leaving it unset would collide with the *next* email-only
        # registration under username's own unique=True constraint.
        user.username = None
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    # Django's AuthenticationForm always names its identity field "username"
    # internally (see plan Key Discoveries) — relabeled here for display only.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

    def confirm_login_allowed(self, user):
        # Overrides (not calls super()) Django's generic "This account is
        # inactive" wording — password already checked successfully at this
        # point, so this is "correct credentials, not verified yet", not a
        # credentials error. Must not leak into the wrong-password path.
        if not user.is_active:
            raise ValidationError(
                'Konto niezweryfikowane — sprawdź maila lub wyślij link ponownie.',
                code='inactive',
            )
