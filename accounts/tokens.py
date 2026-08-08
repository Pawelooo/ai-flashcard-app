from django.core import signing

VERIFICATION_SALT = 'accounts.email-verification'
VERIFICATION_MAX_AGE = 60 * 60 * 24  # 24h


def make_verification_token(user):
    return signing.TimestampSigner(salt=VERIFICATION_SALT).sign(str(user.pk))


def read_verification_token(token):
    """Returns the signed user pk. Raises signing.SignatureExpired / signing.BadSignature."""
    return signing.TimestampSigner(salt=VERIFICATION_SALT).unsign(token, max_age=VERIFICATION_MAX_AGE)
