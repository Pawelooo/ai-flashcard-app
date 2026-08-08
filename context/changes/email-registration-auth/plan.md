
# Email Registration, Verification, Login & Password Reset — Implementation Plan

## Overview

Replace username-based auth with email-based auth across the app: users register with email + password, must click a verification link before they can use the app, log in with email + password, and can reset a forgotten password — all via email. This closes a gap between the PRD (Access Control: "Users log in via email/password") and the current implementation (`UserCreationForm` collects only `username`).

## Current State Analysis

- `config/urls.py:29-36` — `RegisterView` uses Django's built-in `UserCreationForm` (username + password only, no email field) and logs the user in immediately on success.
- `config/urls.py:66-68` — `LoginView`/`RegisterView` are wrapped in `_rate_auth` (`django_ratelimit`, `key='ip'`, `10/m`), which must be preserved.
- No `AUTH_USER_MODEL` override exists — the app uses Django's built-in `auth.User` untouched.
- `flashcards/models.py:22-23,38-39` — `Card.created_by` and `CardReview.user` are `ForeignKey(settings.AUTH_USER_MODEL, ...)`, not a hardcoded `'auth.User'` string. This is what makes a safe `AUTH_USER_MODEL` swap possible without touching `flashcards`' migration history (see Key Discoveries).
- Production (Fly.io + Supabase Postgres) has real registered users. Confirmed during planning: all of them have a blank `email` field, since the current registration form never collected one. A destructive reset of the `auth_user` table is off the table.
- No `EMAIL_BACKEND` is configured anywhere — Django defaults to console-only email, which doesn't reach real users. No email-sending dependency (SMTP creds, Anymail, etc.) exists in `pyproject.toml`.
- `django_ratelimit` is already a dependency and already wired into `MIDDLEWARE` (`config/settings.py:58`) and `RATELIMIT_VIEW`/`RATELIMIT_FAIL_OPEN` (`config/settings.py:130-131`) — the same pattern extends naturally to new rate-limited endpoints (resend-verification, password reset).
- `templates/registration/login.html` and `register.html` render forms generically via a `{% for field in form %}` loop — no per-field custom markup, so swapping the underlying form class requires no template rewrite.

## Desired End State

- A new visitor registers with email + password (email must be unique). Their account is created inactive (`is_active=False`) and a verification email is sent.
- Clicking the verification link activates the account, logs the user in, and redirects to `flashcards:topics`. An expired or tampered link shows an error with a "resend" option.
- Login is by email + password. Wrong credentials show one generic error (no account-enumeration signal). An account that exists but isn't verified yet shows a distinct "check your email" message with a resend link.
- A user who forgot their password can request a reset email and set a new password via a time-limited link (Django's built-in password-reset views, reused as-is).
- Existing (pre-change) accounts, which have no email on file, keep working via their old username + password. On their next login they're nudged (not blocked) to add and verify an email, going forward.
- All of the above is deployed to Fly.io/Supabase without losing a single existing user row, password hash, or `Card`/`CardReview` FK relationship.

### Key Discoveries

- Because `flashcards/models.py` already points its `User` foreign keys at `settings.AUTH_USER_MODEL` (not a literal `'auth.User'` string), Django recorded those historical migrations with a dependency on the **swappable setting**, not a fixed app/model. When `AUTH_USER_MODEL` is changed, Django re-resolves that dependency automatically — `flashcards`' existing 4 migrations need zero edits. This is what makes the swap feasible at all this late in the project.
- The physical `auth_user` table can be preserved untouched (no data copy, no ID remapping) by giving the new `CustomUser` model `Meta.db_table = 'auth_user'` and creating it via `migrations.SeparateDatabaseAndState` (state-only `CreateModel`, no real DDL) followed by a real, separate `AlterField`/data-cleanup migration for the `email` column. This avoids the much higher-risk "create new table, copy every row, repoint FKs" path entirely.
- Django's default login field is internally always named `username` (`AuthenticationForm`'s field), regardless of what value it actually collects. The plan relabels it to "Email" for display but does not rename the field — renaming it would require reimplementing `AuthenticationForm.clean()`.
- `django.contrib.auth.forms.AuthenticationForm.confirm_login_allowed(user)` is the intended hook for turning "correct password, but account not usable yet" into a distinct, non-enumerating error message — it only runs after a successful password check, so the "wrong password" and "not verified yet" messages never leak into each other from the wrong-password path.
- `PasswordResetForm.get_users()` (Django built-in) already filters to `is_active=True` accounts only — an unverified (still-inactive) account silently gets no reset email, which is the correct, already-existing behavior and needs no extra code.

## What We're NOT Doing

- Not touching `is_staff`/`is_superuser` or any admin-role question (FR-007 / roadmap S-03) — out of scope here.
- Not adding social/OAuth login, despite the PRD mentioning it as an option ("email/password or OAuth") — email/password only, per this task's explicit scope.
- Not building a styled HTML verification/reset email — plain text for both, per the must-have/nice-to-have split agreed during planning.
- Not adding a "resend" cooldown countdown UI (progress bar/timer) — the server-side rate limit (1/min) is enforced regardless; the UI just shows the resulting error if hit.
- Not re-verifying or deactivating existing (pre-change) accounts that already had `is_active=True` — they keep working through the transition; adding email is a one-time nudge, not a hard gate.
- Not introducing `django-allauth` or any other auth framework dependency — the scope is small enough that Django's built-in pieces (`AbstractUser`, `PasswordResetView`, `django.core.signing`) cover it without a new dependency.

## Implementation Approach

Four sequential phases. Phase 1 (data model + email infra) must land first since every later phase depends on `CustomUser` existing and email being sendable. Phase 2 (registration + verification) and Phase 3 (login + legacy gate) are tightly coupled (both touch the auth backend and `is_active` semantics) but are split for reviewability. Phase 4 (password reset) is the most isolated — it's almost entirely Django's built-in views — and lands last.

## Critical Implementation Details

**Migration ordering and safety.** The `email` column on the existing `auth_user` table currently allows blanks, and at least one pair of existing rows share the same blank value. Adding a `unique=True` constraint must be preceded by a data migration that converts every blank email (`''`) to `NULL` — Postgres and SQLite both allow multiple `NULL`s under a unique constraint, but not multiple empty strings. Getting this ordering wrong (`AlterField` before the blank→NULL cleanup) will fail the migration against the real data on both local sqlite and Supabase Postgres. This migration must be dry-run against a copy of the production database (or at minimum the local `db.sqlite3`) before it is ever pointed at Fly.io — per `infrastructure.md`'s existing precedent that schema-altering, hard-to-reverse production operations get a manual approval step, this migration is one of them and must not be auto-applied via `fly deploy`'s `release_command` without that check having already happened once against a copy of the real data.

**`is_active` has two different meanings depending on account age.** For brand-new registrations, `is_active=False` is the enforcement mechanism that blocks login until verified. For pre-existing accounts (already `is_active=True` before this change shipped), `is_active` stays `True` through the transition — only `email` starts `NULL` for them. The "nudge to add email" flow must never flip a pre-existing account back to `is_active=False`; doing so would lock out a real, currently-working user over a new, unrelated requirement.

## Phase 1: CustomUser Model & Email Infrastructure

### Overview

Introduce `CustomUser` as `AUTH_USER_MODEL`, mapped onto the existing `auth_user` table with zero data movement, plus the `RESEND`-backed `EMAIL_BACKEND` every later phase needs to send mail.

### Changes Required:

#### 1. New `accounts` app with `CustomUser`

**File**: `accounts/models.py` (new app: `accounts/__init__.py`, `apps.py`, `models.py`)

**Intent**: Define the swapped-in user model so `email` can be required and unique for new users while staying nullable for the not-yet-migrated legacy rows.

**Contract**: `CustomUser(AbstractUser)` with `email = models.EmailField(unique=True, null=True, blank=True)` and `username = models.CharField(max_length=150, unique=True, null=True, blank=True, validators=[UnicodeUsernameValidator()])` (same field as `AbstractUser.username`, just made nullable — new email-only registrations never populate it, so it must not silently default to `''`, which would collide with the *next* email-only registration under the same `unique=True` constraint). `class Meta: db_table = 'auth_user'` — this is the detail that makes the migration below safe; do not remove it.

#### 2. Data-preserving migration

**File**: `accounts/migrations/0001_initial.py`, `accounts/migrations/0002_email_username_unique.py` (new)

**Intent**: Register `CustomUser` in Django's migration state without touching the physical table, then separately clean up and constrain the `email` and `username` columns for real.

**Contract**: `0001_initial.py` uses `migrations.SeparateDatabaseAndState(state_operations=[migrations.CreateModel(... matching CustomUser's fields ...)], database_operations=[])` — no real DDL. `0002_email_username_unique.py` is a real migration: a `RunPython` step that sets `email = NULL` wherever `email = ''` (existing legacy rows), followed by `AlterField('customuser', 'email', models.EmailField(unique=True, null=True, blank=True))` and `AlterField('customuser', 'username', models.CharField(max_length=150, unique=True, null=True, blank=True))` to add the actual constraints. Existing rows keep their real `username` values (it's never blank for pre-change accounts, so no blank-to-null cleanup is needed on that column) — only the column's nullability changes, to make room for future email-only registrations.

```python
def blank_to_null(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.filter(email='').update(email=None)
```

#### 3. Wire the swap + email backend

**File**: `config/settings.py`

**Intent**: Point Django at the new user model and configure outbound email so verification/reset links can actually be delivered.

**Contract**: Add `'accounts'` to `INSTALLED_APPS`. Add `AUTH_USER_MODEL = 'accounts.CustomUser'`. Add `EMAIL_BACKEND`, `EMAIL_HOST = 'smtp.resend.com'`, `EMAIL_PORT = 587`, `EMAIL_HOST_USER = 'resend'`, `EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY')`, `EMAIL_USE_TLS = True`, `DEFAULT_FROM_EMAIL`. Document `RESEND_API_KEY` in `.env.example` alongside the existing `REDIS_URL` entry.

#### 4. Fix concrete `User` imports that break under a swapped model

**File**: `flashcards/tests.py`, `flashcards/management/commands/verify_manual_checks.py`

**Intent**: Both files currently do `from django.contrib.auth.models import User` and call `User.objects.create_user(...)`. Once `AUTH_USER_MODEL` points elsewhere, `auth.models.User` becomes a swapped-out model and any `.objects` access raises `AttributeError: Manager isn't available; 'auth.User' has been swapped for 'accounts.CustomUser'` — silently breaking every test in `flashcards/tests.py` and the management command.

**Contract**: Replace the concrete import with `from django.contrib.auth import get_user_model` and `User = get_user_model()` at module scope, matching the pattern `stats/services.py`/`stats/tests.py` already use correctly.

#### 5. Re-register the admin's Users page for `CustomUser`

**File**: `accounts/admin.py` (new)

**Intent**: `django.contrib.auth.admin` registers Django's built-in `UserAdmin` against the concrete `auth.models.User`, not via `get_user_model()`. After the `AUTH_USER_MODEL` swap, that registration points at a swapped-out model — visiting `/admin/auth/user/` (the content-seeding admin's user list) raises the same swapped-model `AttributeError` as item #4. Without this file, the admin's "Users" section is broken for as long as the swap is in effect.

**Contract**: `from django.contrib import admin; from django.contrib.auth.admin import UserAdmin; from .models import CustomUser` then `admin.site.register(CustomUser, UserAdmin)`.

### Success Criteria:

#### Automated Verification:

- [ ] `uv run python manage.py makemigrations --check` reports no missing migrations
- [ ] `uv run python manage.py migrate` applies cleanly against a fixture-seeded copy of the current schema (existing users with blank email, one with a duplicate blank email)
- [ ] `uv run python manage.py test` passes

#### Manual Verification:

- [ ] Run the migration against a copy of `db.sqlite3` (not the live file) and confirm the 2 existing users are still present with unchanged password hashes and unchanged `id`
- [ ] `CardReview`/`Card` rows still resolve their `user`/`created_by` FK after migration (spot-check via shell)
- [ ] Django shell: `send_mail(...)` using the new `EMAIL_BACKEND` successfully delivers to a real inbox via Resend (using a Resend test/sandbox key, not against production)

**Implementation Note**: Pause here for manual confirmation that the migration is safe on a copy of real data before proceeding — this phase is the one genuinely hard-to-reverse step in the whole plan.

---

## Phase 2: Registration & Email Verification

### Overview

New registrations create an inactive account and require clicking a signed, time-limited email link before the account can be used.

### Changes Required:

#### 1. Registration form

**File**: `accounts/forms.py` (new)

**Intent**: Collect only email + password at registration; reject already-used emails without confirming to the submitter whether the email exists (enumeration protection agreed during planning).

**Contract**: `EmailRegistrationForm(UserCreationForm)` with `Meta.model = CustomUser`, `Meta.fields = ('email',)`. On `save()`, set `is_active=False` and explicitly set `user.username = None` before saving — `CharField.get_default()` returns `''`, not `None`, even when the field is `null=True` (on SQLite/Postgres this only matters for Oracle-style backends), so leaving it unset would still produce a `''`-vs-`''` unique collision on the *second* email-only registration. Duplicate-email submissions must not surface Django's default "user with this email already exists" field error — the view (not the form) handles the generic response (see #3).

#### 2. Verification token helper

**File**: `accounts/tokens.py` (new)

**Intent**: Generate and validate the signed, single-use-by-expiry verification link.

**Contract**: Use `django.core.signing.TimestampSigner` with a dedicated `salt='accounts.email-verification'`, signing `str(user.pk)`. Verification (`max_age=60*60*24`, 24h) raises `SignatureExpired` or `BadSignature` on failure — the view distinguishes "expired" (show resend) from "tampered" (show resend) identically; both just route to the same resend prompt.

#### 3. Views: register, verify, resend

**File**: `accounts/views.py` (new)

**Intent**: Wire the registration → email → verify → auto-login flow, and a separately rate-limited resend endpoint.

**Contract**:
- `RegisterView` (replaces the one currently inline in `config/urls.py`): on valid submission, always show the same "check your email" confirmation page — whether or not the email was already registered (send a distinct "someone tried to register with your email" notice to the existing owner in that case, no new account created). On genuinely new emails, create the inactive user and send the verification email via `django.core.mail.send_mail`.
- `verify_email(request, token)`: unsign via the Phase 2.2 helper; on success, `is_active=True`, `login(request, user)`, redirect to `flashcards:topics`. On failure, render a "link expired/invalid" page with a resend form.
- `resend_verification(request)`: `@ratelimit(key='post:email', rate='1/m', block=True, method=['POST'])`. Always renders the same generic confirmation regardless of whether the submitted email matches an account or is already verified.

#### 4. URLs and templates

**File**: `accounts/urls.py` (new), `config/urls.py`, `templates/registration/check_email.html`, `templates/registration/verify_failed.html`, `templates/emails/verification_email.txt`

**Intent**: Mount the new views under the existing `/accounts/` prefix without breaking the `{% url 'register' %}` references already used in `login.html`/`register.html`.

**Contract**: `config/urls.py` replaces its standalone `path('accounts/register/', ...)` entry with `path('accounts/', include('accounts.urls'))`; `accounts/urls.py` defines `register/` (name=`register`, wrapped in the existing `_rate_auth`), `verify/<str:token>/`, `resend-verification/`. Templates follow the existing plain Bootstrap-form-loop style already used by `login.html`/`register.html`.

### Success Criteria:

#### Automated Verification:

- [ ] `uv run python manage.py test` passes
- [ ] Registering creates an inactive user and exactly one outbound email (`django.core.mail.outbox`)
- [ ] Registering with an already-registered email does not create a second user and shows the same generic confirmation as a successful registration
- [ ] A valid verification token activates the account and logs the user in
- [ ] An expired verification token is rejected and shows the resend option
- [ ] A tampered verification token is rejected
- [ ] Hitting resend twice within a minute for the same email returns 429 on the second attempt

#### Manual Verification:

- [ ] Register with a real inbox, receive the email via Resend, click the link, land logged-in on the topics page
- [ ] Confirm the email's "check your email" screen and the resend flow read sensibly in the UI

---

## Phase 3: Email Login & Legacy Account Gate

### Overview

Switch login to email + password, add the custom auth backend and its `confirm_login_allowed` messaging, and nudge (not block) pre-existing accounts to add an email.

### Changes Required:

#### 1. Authentication backend

**File**: `accounts/backends.py` (new)

**Intent**: Authenticate by email first, falling back to the legacy `username` for pre-existing accounts that have no email yet — password check happens regardless of `is_active`, so `confirm_login_allowed` (see #2) can distinguish "wrong credentials" from "correct credentials, unverified."

**Contract**: `EmailOrUsernameBackend(ModelBackend)` overriding `authenticate(request, username=None, password=None, **kwargs)`: look up `CustomUser` by `email__iexact=username`, falling back to `username=username` if no email match; check `user.check_password(password)`; return the user regardless of `is_active` (unlike the base `ModelBackend`, which would filter it out here — the `is_active` gate moves to `confirm_login_allowed` instead, per #2).

#### 2. Login form and messaging

**File**: `accounts/forms.py`, `config/settings.py`, `config/urls.py`

**Intent**: Relabel the login field as "Email" and turn "correct password, inactive account" into a distinct, non-enumerating message instead of Django's generic inactive-account wording.

**Contract**: `EmailAuthenticationForm(AuthenticationForm)` setting `self.fields['username'].label = 'Email'` in `__init__`, and overriding `confirm_login_allowed(user)` to raise a custom `ValidationError` ("Konto niezweryfikowane — sprawdź maila lub wyślij link ponownie.") when `not user.is_active`, instead of calling `super()`. `config/settings.py` sets `AUTHENTICATION_BACKENDS = ['accounts.backends.EmailOrUsernameBackend']`. `config/urls.py`'s `LoginView.as_view(authentication_form=EmailAuthenticationForm)`, still wrapped in the existing `_rate_auth`.

#### 3. Legacy account email gate

**File**: `accounts/views.py`, `accounts/middleware.py` (new), `config/settings.py`

**Intent**: Once a pre-existing account (email still `NULL`) logs in via its legacy username, nudge it — on every request until resolved — to add and verify an email, without blocking access in the meantime.

**Contract**: `RequireEmailMiddleware` — for an authenticated request where `request.user.email` is falsy, redirect to `accounts:complete_email` unless the request path is already the complete-email page, the verification/resend endpoints, the logout URL, or `/admin/` (the admin's content-seeding workflow must stay usable for legacy staff accounts without an email — this is a "nudge, don't block" middleware, and blocking every admin page would contradict that). `complete_email` view: a simple form collecting a new email; on submit, set `user.email` immediately (this is what stops the middleware from nagging further) and send a verification email reusing the Phase 2.2 token helper — but do NOT set `is_active=False`, since the account was already active before this change (see Critical Implementation Details).

### Success Criteria:

#### Automated Verification:

- [ ] `uv run python manage.py test` passes
- [ ] `uv run python manage.py check` reports 0 issues
- [ ] Login with correct email + password succeeds for a verified account
- [ ] Login with wrong email or wrong password shows one identical generic error in both cases
- [ ] Login with correct credentials for an unverified (new) account shows the distinct "check your email" message, not the generic one
- [ ] A legacy account (email `NULL`, `is_active=True`) still logs in via its old username + password
- [ ] A logged-in legacy account with no email is redirected to the complete-email page for any other URL, and stays `is_active=True` throughout

#### Manual Verification:

- [ ] Confirm on a copy of prod-like data that an existing account can still log in and is guided to add an email without ever being locked out

---

## Phase 4: Password Reset

### Overview

Reuse Django's built-in password-reset views end to end, on the new `CustomUser`/email backend, with the same Resend email backend and rate-limiting pattern already established.

### Changes Required:

#### 1. Password reset URLs

**File**: `config/urls.py`

**Intent**: Wire Django's four built-in password-reset views using their default template-name conventions, so no `template_name`/`email_template_name` kwargs are needed beyond what Django already expects.

**Contract**: `password-reset/` → `_rate_auth(auth_views.PasswordResetView.as_view())`, `password-reset/done/` → `PasswordResetDoneView`, `password-reset/confirm/<uidb64>/<token>/` → `PasswordResetConfirmView`, `password-reset/complete/` → `PasswordResetCompleteView`. `_rate_auth` (already `key='ip', rate='10/m'`) applies to the request-a-reset endpoint only, matching the existing login/register abuse-prevention pattern.

#### 2. Templates

**File**: `templates/registration/password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`, `password_reset_email.html`, `password_reset_subject.txt`

**Intent**: Match Django's default template-name lookup exactly (these are the conventional names Django's views resolve automatically) and follow the existing plain Bootstrap-form-loop style.

**Contract**: `password_reset_email.html` is plain text content despite the `.html` extension — this is Django's own naming convention, not a signal that HTML formatting is expected. Add a "Zapomniałeś hasła?" link to `login.html` pointing at the new `password_reset` URL name.

### Success Criteria:

#### Automated Verification:

- [ ] `uv run python manage.py test` passes
- [ ] Requesting a reset for a verified (`is_active=True`) account's email sends exactly one email
- [ ] Requesting a reset for an unverified account's email sends no email (Django's built-in `is_active` filter — already correct, verify it holds)
- [ ] A valid reset link allows setting a new password, and the new password logs in afterward
- [ ] An expired or tampered reset link is rejected

#### Manual Verification:

- [ ] Full manual round-trip via Resend: request reset, receive email, set new password, log in with it

---

## Testing Strategy

### Unit Tests:

- Duplicate-email registration is rejected (no second user created) and shows the same generic message as success.
- Unverified user cannot log in and sees the distinct message; verified user can.
- Expired and tampered verification tokens are both rejected.
- Resend-verification is rate-limited to 1/min per submitted email, independent of requesting IP.
- Legacy account (no email) logs in via username, is redirected to complete-email for other pages, stays active throughout.
- Password reset respects `is_active` (no email to unverified accounts) and the confirm link changes the password.

### Manual Testing Steps:

1. Run the Phase 1 migration against a copy of `db.sqlite3` and confirm existing users/passwords/FKs are intact.
2. Register a new account with a real inbox; receive and click the verification email; confirm auto-login and redirect.
3. Try registering the same email again; confirm the generic response and that the existing owner (not the attacker) gets a notice.
4. Log in with the wrong password; confirm the generic error.
5. Log in as the still-unverified account from step 2 before clicking the link (use a second registration); confirm the distinct "check your email" message.
6. Log in as a legacy (pre-migration) account; confirm redirect to complete-email and that it never gets logged out.
7. Request a password reset, receive the email, set a new password, log in with it.

## Performance Considerations

All new endpoints are low-traffic, auth-adjacent paths (register, verify, resend, reset) already covered by the existing rate-limiting infrastructure; no caching or query-optimization concerns apply.

## Migration Notes

The Phase 1 migration is the only genuinely hard-to-reverse step in this plan — it alters the live `auth_user` table's `email` column. Per the existing production-approval precedent in `infrastructure.md` (SECRET_KEY rotation, scaling to zero, etc. require a human), this migration must be run once against a copy of the production database (or, at minimum, the local `db.sqlite3`) before `fly deploy`'s `release_command` is allowed to apply it to the real Supabase database. Rollback, if needed post-deploy, is reverting the code deploy and running `manage.py migrate accounts 0000` — this un-registers the swapped model state but does not undo the `email` column's `NULL`-backfill or its unique constraint; a full rollback additionally requires manually dropping that constraint.

## References

- `config/urls.py:29-36,56-68` — current `RegisterView`, `handler429`, and `_rate_auth` wiring being extended
- `flashcards/models.py:22-23,38-39` — `settings.AUTH_USER_MODEL` FK usage that makes the swap safe
- `config/settings.py:130-131` — existing `RATELIMIT_FAIL_OPEN`/`RATELIMIT_VIEW` pattern reused for new endpoints
- `context/foundation/prd.md` (Access Control) — "Users log in via email/password or OAuth" is the requirement this plan fulfills
- `context/foundation/infrastructure.md` (Approval section) — precedent for treating hard-to-reverse production operations as requiring manual confirmation

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: CustomUser Model & Email Infrastructure

#### Automated

- [x] 1.1 `manage.py makemigrations --check` reports no missing migrations — 45df554
- [x] 1.2 `manage.py migrate` applies cleanly against fixture-seeded copy of current schema — 45df554
- [x] 1.3 `manage.py test` passes — 45df554

#### Manual

- [x] 1.4 Migration against a copy of `db.sqlite3` preserves existing users/passwords/IDs — 45df554
- [x] 1.5 `CardReview`/`Card` FKs still resolve after migration — 45df554
- [x] 1.6 Real email delivery confirmed via Resend sandbox key — 45df554

### Phase 2: Registration & Email Verification

#### Automated

- [x] 2.1 `manage.py test` passes — 61ac2fe
- [x] 2.2 Registration creates inactive user + exactly one outbound email — 61ac2fe
- [x] 2.3 Duplicate-email registration creates no second user, shows generic message — 61ac2fe
- [x] 2.4 Valid verification token activates account and logs in — 61ac2fe
- [x] 2.5 Expired verification token rejected, resend option shown — 61ac2fe
- [x] 2.6 Tampered verification token rejected — 61ac2fe
- [x] 2.7 Resend rate-limited to 1/min per email — 61ac2fe

#### Manual

- [x] 2.8 Real-inbox registration → verification → auto-login round trip — 61ac2fe
- [x] 2.9 Check-email and resend screens read sensibly — 61ac2fe

### Phase 3: Email Login & Legacy Account Gate

#### Automated

- [x] 3.1 `manage.py test` passes — 375ed95
- [x] 3.2 `manage.py check` reports 0 issues — 375ed95
- [x] 3.3 Correct email+password login succeeds for verified account — 375ed95
- [x] 3.4 Wrong email or password shows identical generic error — 375ed95
- [x] 3.5 Correct credentials for unverified account show distinct message — 375ed95
- [x] 3.6 Legacy account logs in via old username — 375ed95
- [x] 3.7 Legacy account redirected to complete-email, stays active — 375ed95

#### Manual

- [x] 3.8 Prod-like legacy account never locked out, guided to add email — 375ed95

### Phase 4: Password Reset

#### Automated

- [ ] 4.1 `manage.py test` passes
- [ ] 4.2 Reset email sent for verified account
- [ ] 4.3 No reset email sent for unverified account
- [ ] 4.4 Valid reset link changes password and new password logs in
- [ ] 4.5 Expired/tampered reset link rejected

#### Manual

- [ ] 4.6 Full Resend round trip: request → email → set password → log in
