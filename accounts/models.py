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

    # Explicit `through` models below, not Django's auto-created M2M through
    # tables: Django names the auto through table after Meta.db_table (so it
    # would correctly land on the pre-existing `auth_user_groups` /
    # `auth_user_user_permissions` tables here), but it names the FK *column*
    # after the defining model's class name (`customuser_id`), independent of
    # db_table. Those tables' actual columns — inherited unchanged from the
    # original auth.User migration — are `user_id`, not `customuser_id`.
    # Without this override, any ORM access to `.groups`/`.user_permissions`
    # (including `user.delete()`'s cascade collector and the admin's user
    # change form) raises `OperationalError: no such column ...customuser_id`.
    groups = models.ManyToManyField(
        'auth.Group',
        through='accounts.CustomUserGroups',
        blank=True,
        related_name='user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        through='accounts.CustomUserUserPermissions',
        blank=True,
        related_name='user_set',
        related_query_name='user',
    )

    objects = CustomUserManager()

    class Meta:
        db_table = 'auth_user'


class CustomUserGroups(models.Model):
    customuser = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, db_column='user_id')
    group = models.ForeignKey('auth.Group', on_delete=models.CASCADE, db_column='group_id')

    class Meta:
        db_table = 'auth_user_groups'
        unique_together = [('customuser', 'group')]


class CustomUserUserPermissions(models.Model):
    customuser = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, db_column='user_id')
    permission = models.ForeignKey('auth.Permission', on_delete=models.CASCADE, db_column='permission_id')

    class Meta:
        db_table = 'auth_user_user_permissions'
        unique_together = [('customuser', 'permission')]
