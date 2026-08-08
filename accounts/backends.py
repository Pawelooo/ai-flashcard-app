from django.contrib.auth.backends import ModelBackend

from .models import CustomUser


class EmailOrUsernameBackend(ModelBackend):
    # Looks up by email first (the new login flow), falling back to username for
    # legacy accounts that have no email yet. Returns the user regardless of
    # is_active — unlike ModelBackend, which filters inactive users out here —
    # so EmailAuthenticationForm.confirm_login_allowed() can tell "wrong
    # credentials" apart from "correct credentials, unverified account".
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        user = CustomUser.objects.filter(email__iexact=username).first()
        if user is None:
            user = CustomUser.objects.filter(username=username).first()
        if user is None:
            # Run the default password hasher once anyway, to reduce the
            # timing difference between an existing and a nonexistent user
            # (same rationale as ModelBackend.authenticate(), Django #20760).
            CustomUser().set_password(password)
            return None
        if not user.check_password(password):
            return None
        return user
