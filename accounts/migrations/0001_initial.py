# Hand-written per plan Phase 1 contract (not a raw `makemigrations` output).
#
# CustomUser reuses the physical `auth_user` table (Meta.db_table='auth_user'). On an
# EXISTING database (local db.sqlite3, Supabase prod) that table already physically
# exists — created long ago by django.contrib.auth's own migration, back before
# AUTH_USER_MODEL pointed anywhere else — so no real CREATE TABLE is needed there.
#
# But on a BRAND NEW database (manage.py test's throwaway DB, CI, a fresh clone), that
# table is never created by anyone: auth.0001_initial's own CreateModel(User) is a no-op
# there because Django's migration executor skips CreateModel for any model that's
# currently swapped out (`router.allow_migrate_model` returns False once AUTH_USER_MODEL
# points at accounts.CustomUser) — regardless of whether the database is old or new.
# Verified empirically: migrating a fresh empty sqlite file raised
# `OperationalError: no such table: auth_user` on this migration before this fix.
#
# So database_operations can't simply be `[]` — it must create the table for real, but
# ONLY if it doesn't already exist (checked via schema introspection), which plain
# CreateModel/SeparateDatabaseAndState can't express conditionally. A RunPython step
# calling schema_editor.create_model() directly is the standard way to do a conditional
# CREATE TABLE inside a migration.
#
# groups/user_permissions: Django names a M2M field's auto-created through table as
# `<db_table>_<field_name>`, not `<app_label>_<model_name>_<field_name>` — since
# CustomUser sets `db_table='auth_user'`, its through tables DO land on the correct
# names (`auth_user_groups` / `auth_user_user_permissions`). BUT the through table's FK
# *column* name is derived separately, from the defining model's class name
# (`customuser_id`), regardless of db_table. The physical columns on these pre-existing
# tables — inherited unchanged from auth.User's original migration — are `user_id`, not
# `customuser_id`. Verified empirically: `user.delete()` (whose cascade collector reads
# `.groups`) raised `OperationalError: no such column: auth_user_groups.customuser_id`
# before this fix. CustomUser therefore declares `groups`/`user_permissions` with an
# explicit `through=` to `CustomUserGroups`/`CustomUserUserPermissions` below, each with
# `db_column='user_id'` to match. Both the base table and these two through tables are
# part of the SAME conditional "create if missing" step (existing DBs already have all
# three, empty, from auth.User's original migration) — NOT a separate always-real
# AddField, which would try to CREATE TABLE on an existing database where it already
# exists. The bootstrap-only `CustomUserBootstrap` model (fresh-DB path) mirrors this
# same explicit-through-table structure via `CustomUserBootstrapGroups`/
# `CustomUserBootstrapUserPermissions` below, so a genuinely fresh database (CI, a new
# clone, `manage.py test`'s throwaway DB) gets the same `user_id`/`group_id`/
# `permission_id` column names instead of Django's default class-name-derived ones.
#
# IMPORTANT: `email`/`username` are deliberately declared here in their CURRENT physical
# shape (email: not unique, not null; username: unique, not null) rather than the final
# shape in accounts/models.py. If this migration's state already matched the final
# null=True/unique=True shape, 0002's AlterField would see "no change" between its own
# from-state and to-state and would silently skip the real ALTER TABLE — the whole point
# of 0002 is to be the one migration where the state visibly transitions from the old
# shape to the new one, so Django actually emits the DDL. `makemigrations --check` still
# passes because only the *last* migration in the chain needs to match models.py, not
# every intermediate step.

import accounts.models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.apps import apps as global_apps
from django.db import migrations, models
from django.db.migrations.state import ModelState, ProjectState


def create_auth_user_tables_if_missing(apps, schema_editor):
    # `apps.get_model('accounts', 'CustomUser')` isn't usable here — a
    # SeparateDatabaseAndState's database_operations run against a from/to state chain
    # that's deliberately isolated from state_operations' effects, so 'accounts' is never
    # registered in it ("No installed app with label 'accounts'").
    #
    # A plain `class Foo(models.Model): ...` defined inside this function doesn't help
    # either — Django's model metaclass registers every Model subclass into the GLOBAL
    # app registry the instant it's defined, permanently, for the rest of the process.
    # `manage.py test` runs this migration for real while building its test database,
    # which registers that throwaway class globally — then later system checks see it
    # sitting alongside the real accounts.CustomUser, both claiming db_table='auth_user',
    # and fail with the exact "db_table used by multiple models" error this whole
    # migration exists to avoid. Verified empirically.
    #
    # The fix is to build the throwaway model inside its own isolated `ProjectState`
    # (via `StateApps`, the same mechanism Django's own migration executor uses for
    # state_operations) instead of the global registry — `state.apps.get_model(...)`
    # returns a model class that's real enough for `schema_editor.create_model()` but
    # invisible to the global app registry and its system checks.
    connection = schema_editor.connection
    if 'auth_user' in connection.introspection.table_names():
        return  # existing database — this whole table family predates this migration

    state = ProjectState.from_apps(global_apps)
    state.add_model(ModelState(
        app_label='accounts',
        name='CustomUserBootstrap',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('password', models.CharField(max_length=128)),
            ('last_login', models.DateTimeField(blank=True, null=True)),
            ('is_superuser', models.BooleanField(default=False)),
            ('first_name', models.CharField(blank=True, max_length=150)),
            ('last_name', models.CharField(blank=True, max_length=150)),
            ('is_staff', models.BooleanField(default=False)),
            ('is_active', models.BooleanField(default=True)),
            ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
            ('username', models.CharField(
                max_length=150,
                unique=True,
                validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
            )),
            ('email', models.EmailField(blank=True, max_length=254)),
            # No groups/user_permissions M2M fields here — Django's default
            # auto-created through table for an M2M field on this model would name
            # its FK column `customuserbootstrap_id`, the same class-name-derived
            # mismatch this whole migration exists to avoid (see module docstring).
            # The two through tables are created explicitly below instead, with the
            # matching `user_id` column, and never appear as a field on this model at
            # all — it's discarded immediately after use, so it needs no relation
            # back to them.
        ],
        options={'db_table': 'auth_user'},
        bases=(models.Model,),
    ))
    # Explicit through-table stand-ins for `auth_user_groups` / `auth_user_user_permissions`,
    # matching CustomUserGroups/CustomUserUserPermissions in accounts/models.py — same
    # `user_id`/`group_id`/`permission_id` column names, not Django's class-name-derived
    # defaults. related_name='+': thrown away immediately, must not create a reverse
    # accessor on auth.Group/auth.Permission.
    state.add_model(ModelState(
        app_label='accounts',
        name='CustomUserBootstrapGroups',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('customuserbootstrap', models.ForeignKey('accounts.CustomUserBootstrap', on_delete=models.CASCADE, db_column='user_id')),
            ('group', models.ForeignKey('auth.Group', on_delete=models.CASCADE, db_column='group_id', related_name='+')),
        ],
        options={'db_table': 'auth_user_groups'},
        bases=(models.Model,),
    ))
    state.add_model(ModelState(
        app_label='accounts',
        name='CustomUserBootstrapUserPermissions',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('customuserbootstrap', models.ForeignKey('accounts.CustomUserBootstrap', on_delete=models.CASCADE, db_column='user_id')),
            ('permission', models.ForeignKey('auth.Permission', on_delete=models.CASCADE, db_column='permission_id', related_name='+')),
        ],
        options={'db_table': 'auth_user_user_permissions'},
        bases=(models.Model,),
    ))
    CustomUserBootstrap = state.apps.get_model('accounts', 'CustomUserBootstrap')
    schema_editor.create_model(CustomUserBootstrap)
    schema_editor.create_model(state.apps.get_model('accounts', 'CustomUserBootstrapGroups'))
    schema_editor.create_model(state.apps.get_model('accounts', 'CustomUserBootstrapUserPermissions'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='CustomUser',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('password', models.CharField(max_length=128, verbose_name='password')),
                        ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                        ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                        ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                        ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                        ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                        ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                        ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                        ('username', models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                        ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                        ('groups', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', through='accounts.CustomUserGroups', to='auth.group')),
                        ('user_permissions', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', through='accounts.CustomUserUserPermissions', to='auth.permission')),
                    ],
                    options={
                        'db_table': 'auth_user',
                    },
                    managers=[
                        ('objects', accounts.models.CustomUserManager()),
                    ],
                ),
                migrations.CreateModel(
                    name='CustomUserGroups',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('customuser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser', db_column='user_id')),
                        ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group', db_column='group_id')),
                    ],
                    options={
                        'db_table': 'auth_user_groups',
                        'unique_together': {('customuser', 'group')},
                    },
                ),
                migrations.CreateModel(
                    name='CustomUserUserPermissions',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('customuser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser', db_column='user_id')),
                        ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission', db_column='permission_id')),
                    ],
                    options={
                        'db_table': 'auth_user_user_permissions',
                        'unique_together': {('customuser', 'permission')},
                    },
                ),
            ],
            database_operations=[
                migrations.RunPython(create_auth_user_tables_if_missing, reverse_code=reverse_noop),
            ],
        ),
    ]
