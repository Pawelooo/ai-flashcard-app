# Real migration (not state-only): converts legacy blank emails to NULL, then adds the
# actual `unique=True`/`null=True` constraints on `email` and `null=True` on `username`.
#
# Ordering: three separate steps for `email`, not two.
#   1. AlterField to null=True ONLY (no unique yet) — a NOT NULL column physically
#      rejects `UPDATE ... SET email = NULL` regardless of what the ORM/migration state
#      says, so the column must be made nullable *before* the data cleanup can run at
#      all. Verified empirically: running the cleanup before this step raised
#      `IntegrityError: NOT NULL constraint failed: auth_user.email`.
#   2. RunPython: now-legal blank -> NULL cleanup.
#   3. AlterField to add unique=True — safe now that step 2 removed every duplicate ''
#      (Postgres and SQLite both allow multiple NULLs under a unique constraint, but not
#      multiple empty strings, and at least one pair of existing rows share a blank
#      email).
#
# `username` needs only one AlterField (null=True, unique=True already holds and stays
# unchanged) — no existing row has a blank username, confirmed before writing this
# migration, so there's no analogous ordering problem there.

import django.contrib.auth.validators
from django.db import migrations, models


def blank_to_null(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.filter(email='').update(email=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.RunPython(blank_to_null, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()]),
        ),
    ]
