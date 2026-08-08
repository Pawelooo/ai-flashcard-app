"""
Required one-time step before `manage.py migrate` on any database that already had
migrations applied before the accounts.CustomUser swap (local db.sqlite3, production
Supabase) — run it once, then run `manage.py migrate` normally.

Why this is needed: django.contrib.admin's own migration (admin.0001_initial) depends
on `migrations.swappable_dependency(settings.AUTH_USER_MODEL)`, which now resolves to
('accounts', '0001_initial') instead of the 'auth' app. On a database where admin's
migration was already applied *before* the accounts app existed, Django's migration
consistency check refuses to proceed at all ("Migration admin.0001_initial is applied
before its dependency accounts.0001_initial") — and this happens before `migrate` even
looks at its own arguments, so `--fake` on the CLI can't reach it either. The fix is to
record accounts.0001_initial as applied directly via the migration recorder, bypassing
that check exactly once.

On a brand-new database (nothing applied yet, e.g. a fresh `manage.py test` run or CI),
this command is a safe no-op: recorded migrations only exist if `manage.py migrate` has
already run, and the freshness check below (auth_user table already existing) protects
against ever needing this in that case.

Safe to re-run: does nothing if accounts.0001_initial is already recorded, or if
auth_user doesn't exist yet (i.e. this is actually a fresh database).
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = (
        "One-time fix-up for pre-existing databases migrating onto accounts.CustomUser: "
        "records accounts.0001_initial as already applied so Django's migration "
        "consistency check doesn't block on admin's now-retroactive dependency on it."
    )

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()

        if ('accounts', '0001_initial') in applied:
            self.stdout.write("accounts.0001_initial already recorded — nothing to do.")
            return

        if 'auth_user' not in connection.introspection.table_names():
            self.stdout.write(
                "auth_user table doesn't exist yet — this is a fresh database, "
                "`manage.py migrate` will handle everything normally. Nothing to do."
            )
            return

        recorder.record_applied('accounts', '0001_initial')
        self.stdout.write(self.style.SUCCESS(
            "Recorded accounts.0001_initial as applied. Now run `manage.py migrate` normally."
        ))
