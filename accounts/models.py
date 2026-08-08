from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class CustomUserManager(UserManager):
    # UserManager.normalize_email() (via BaseUserManager) coerces a falsy email to
    # `''`, not `None` — harmless for the built-in auth.User (email isn't unique
    # there), but fatal here: `email` is `unique=True, null=True`, so every
    # create_user() call that omits an email (most of flashcards' test fixtures,
    # `createsuperuser` without --email, etc.) would collide on `''` after the
    # first one. Normalizing "no email" to `None` keeps multiple such users legal,
    # since SQLite/Postgres both allow multiple NULLs under a unique constraint.
    @classmethod
    def normalize_email(cls, email):
        if not email:
            return None
        return super().normalize_email(email)


class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(unique=True, null=True, blank=True)

    objects = CustomUserManager()

    class Meta:
        db_table = 'auth_user'
