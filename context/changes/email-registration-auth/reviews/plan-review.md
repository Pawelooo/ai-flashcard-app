<!-- PLAN-REVIEW-REPORT -->
# Plan Review: Email Registration, Verification, Login & Password Reset

- **Plan**: context/changes/email-registration-auth/plan.md
- **Mode**: Deep
- **Date**: 2026-07-28
- **Verdict**: REVISE → SOUND after triage fixes
- **Findings**: 3 critical, 2 warnings, 1 observation

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| End-State Alignment | WARNING |
| Lean Execution | PASS |
| Architectural Fitness | WARNING |
| Blind Spots | FAIL |
| Plan Completeness | WARNING |

## Grounding

6/6 paths ✓ (config/urls.py, config/settings.py, flashcards/models.py, templates/registration/login.html, templates/registration/register.html, pyproject.toml), 4/4 symbols ✓ (settings.AUTH_USER_MODEL FK usage, django_ratelimit wiring, RATELIMIT_FAIL_OPEN/VIEW, swappable_dependency in flashcards/migrations/0004), brief↔plan ✓.

## Findings

### F1 — Second self-registered user collides on username=''

- **Severity**: ❌ CRITICAL
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: End-State Alignment / Blind Spots
- **Location**: Phase 2.1 — Registration form (`accounts/forms.py`)
- **Detail**: `EmailRegistrationForm.Meta.fields = ('email',)` never touches `username`. `CustomUser` inherited `AbstractUser.username` (`unique=True`, no `null=True`) unchanged. `CharField.get_default()` returns `''` when unset, so every email-only registration creates `username=''`. First registration succeeds; the second collides on the unique constraint and fails.
- **Fix A**: Set `user.username = user.email` in `EmailRegistrationForm.save()` — minimal, no new migration, but makes `username` a redundant copy of `email`.
- **Fix B ⭐ (chosen)**: Make `username` nullable via the same blank→NULL migration pattern already used for `email`, plus explicitly set `user.username = None` in `EmailRegistrationForm.save()` (required because `CharField.get_default()` still returns `''`, not `None`, on SQLite/Postgres even when the field is `null=True`).
- **Decision**: FIXED (Fix B) — applied to `plan.md`: CustomUser contract now includes `username = CharField(..., null=True, blank=True, ...)`; migration `0002_email_username_unique.py` now also cleans/constrains `username`; `EmailRegistrationForm.save()` contract now explicitly sets `username = None`.

### F2 — `manage.py test` will fail: concrete `User` imports break under the swap

- **Severity**: ❌ CRITICAL
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: End-State Alignment / Plan Completeness
- **Location**: Phase 1 — not originally listed in "Changes Required"
- **Detail**: `flashcards/tests.py:2` and `flashcards/management/commands/verify_manual_checks.py:9` import `django.contrib.auth.models.User` directly and call `.objects.create_user(...)`. Post-swap this raises `AttributeError: Manager isn't available; 'auth.User' has been swapped for 'accounts.CustomUser'`, breaking Phase 1's own "`manage.py test` passes" criterion. `stats/services.py`/`stats/tests.py` already use `get_user_model()` correctly.
- **Fix**: Replace the concrete import with `get_user_model()` in both files.
- **Decision**: FIXED — added as item #4 in Phase 1's "Changes Required" in `plan.md`.

### F3 — Django admin's Users page breaks after the swap

- **Severity**: ❌ CRITICAL
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots / Plan Completeness
- **Location**: Phase 1 — no `accounts/admin.py` in the original plan
- **Detail**: `django.contrib.auth.admin` registers `UserAdmin` against the concrete `auth.models.User` unconditionally (not via `get_user_model()`). After the swap, `/admin/auth/user/` hits the same swapped-model `AttributeError` as F2. CLAUDE.md states the admin panel is actively used for content seeding.
- **Fix**: Add `accounts/admin.py` registering `admin.site.register(CustomUser, UserAdmin)`.
- **Decision**: FIXED — added as item #5 in Phase 1's "Changes Required" in `plan.md`.

### F4 — Legacy email-nudge middleware has no `/admin/` exclusion

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots
- **Location**: Phase 3.3 — `RequireEmailMiddleware`
- **Detail**: A legacy staff account (email `NULL`) used for the admin's content-seeding workflow would get redirected away from every admin page until it adds an email — contradicting the plan's own "nudge, don't block" principle for a workflow that's actually in active use.
- **Fix**: Add `/admin/` to `RequireEmailMiddleware`'s exclusion list.
- **Decision**: FIXED — `plan.md` Phase 3.3 contract updated to exclude `/admin/`.

### F5 — Post-swap `username` still surfaced to end users (nav, leaderboard tie-break)

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Blind Spots
- **Location**: `templates/base.html:237`, `stats/services.py:25`
- **Detail**: With F1's fix, new email-only users have `username=NULL`. `templates/base.html:237` renders `{{ user.username }}` in the nav; `stats/services.py:25` tie-breaks the leaderboard by `username`. Both would show/behave oddly for new users. Not mentioned anywhere in the original plan.
- **Decision**: ACCEPTED RISK — not fixed in the plan; to be handled during implementation.

### F6 — Stale e2e bytecode for a registration-flow test with no source

- **Severity**: 🔵 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots
- **Location**: `e2e/__pycache__/test_risk6_registration_flow.*.pyc`
- **Detail**: Compiled bytecode exists for a registration-flow e2e test but the `.py` source is absent from the working tree, and `git log` shows it was never committed — likely a local scratch file, not a data-loss incident. No current e2e coverage exists for the registration flow.
- **Decision**: ACCEPTED RISK — a fresh e2e test may be written during Phase 2/3 manual verification; no plan change made.
