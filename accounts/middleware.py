from django.shortcuts import redirect
from django.urls import reverse

# Prefix, not a fixed path — verify/<token>/ carries a dynamic token segment.
_VERIFY_PREFIX = '/accounts/verify/'
_ADMIN_PREFIX = '/admin/'


class RequireEmailMiddleware:
    # Nudges (not blocks) a legacy account (real, pre-existing, is_active=True,
    # email still NULL) toward adding an email, on every request until resolved.
    # Must never touch is_active — that would lock out a currently-working user
    # over a new, unrelated requirement (see plan's Critical Implementation Details).
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and not user.email
            and not request.path.startswith(_ADMIN_PREFIX)
            and not request.path.startswith(_VERIFY_PREFIX)
            and request.path
            not in {reverse('complete_email'), reverse('resend_verification'), reverse('logout')}
        ):
            return redirect('complete_email')
        return self.get_response(request)
