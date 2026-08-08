from django.contrib.auth.forms import UserCreationForm

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
