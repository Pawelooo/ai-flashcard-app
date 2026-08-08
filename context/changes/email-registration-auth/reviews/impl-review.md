<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Email Registration, Verification, Login & Password Reset

- **Plan**: context/changes/email-registration-auth/plan.md
- **Scope**: Full plan — Phases 1–4
- **Date**: 2026-08-08
- **Verdict**: NEEDS ATTENTION
- **Findings**: 0 critical, 5 warnings, 3 observations

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | WARNING |
| Scope Discipline | WARNING |
| Safety & Quality | WARNING |
| Architecture | PASS |
| Pattern Consistency | WARNING |
| Success Criteria | PASS |

## Triage outcome (2026-08-08)

Fixed: F1, F2, F3, F4, F5, F6, F7 (7). Skipped: F8 (1, user's explicit call — see its Decision line).
All 88 tests + `manage.py check` re-verified green after every fix. See per-finding `Decision` lines below for exact fix details, which in a few cases (F3, F5) extended slightly beyond the finding's own location for consistency.

## Success criteria verification (re-run 2026-08-08)

- `manage.py makemigrations --check` — no changes detected
- `manage.py check` — 0 issues
- `manage.py test` — 88/88 passing
- All manual verification items across Phases 1–4 confirmed by user during implementation

## Findings

### F1 — Zalogowany legacy-user może sprawdzić dowolny email przez complete-email

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: accounts/views.py:76-83 (`CompleteEmailForm.clean_email`)
- **Detail**: `RegisterView.form_valid` deliberately shows an identical response whether or not the email already exists (enumeration protection, covered by `test_duplicate_email_registration_creates_no_second_user_and_shows_generic_page`). `CompleteEmailForm.clean_email` does the opposite: it raises a field-level "Ten adres email jest już używany" error when the email exists. Any authenticated legacy account (every pre-existing account is one) can therefore probe arbitrary emails via `/accounts/complete-email/` and get a direct yes/no signal — defeating the enumeration protection built elsewhere in the same feature.
- **Fix A ⭐ Recommended**: Mirror `RegisterView` — always accept the submission; on collision, silently notify the existing owner instead of raising a field error.
  - Strength: Consistent with the rest of the feature; closes a real enumeration vector.
  - Tradeoff: Unusual UX — the legacy user won't immediately learn the email is taken; needs a distinct notice template/copy.
  - Confidence: HIGH — identical pattern already works in `RegisterView`.
  - Blind spot: No test currently covers this path.
- **Fix B**: Keep the field error; accept the risk as lower-severity (attacker must already hold an active account, a higher bar than anonymous registration probing).
  - Strength: Zero code change, simpler UX.
  - Tradeoff: Keeps a real, if smaller, enumeration gap.
  - Confidence: MEDIUM — depends how much consistency of protection matters here.
  - Blind spot: Haven't checked how many legacy accounts exist in production.
- **Decision**: FIXED via Fix A

### F2 — Brak zabezpieczenia przed timing-attack w EmailOrUsernameBackend

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: accounts/backends.py:12-22
- **Detail**: When no user matches, `authenticate()` returns `None` immediately without calling `check_password()`. Django's own `ModelBackend.authenticate()` deliberately hashes a dummy password on `DoesNotExist` "to reduce the timing difference between an existing and a nonexistent user" (Django source, ticket #20760). This backend drops that mitigation — response-time measurement can distinguish "no such account" from "wrong password" even though the login form shows an identical error message.
- **Fix**: Add an `else` branch that runs a dummy `set_password`/hasher check when no user is found, matching `ModelBackend.authenticate()`.
- **Decision**: FIXED

### F3 — Wyścig przy równoczesnej rejestracji tego samego emaila

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: accounts/views.py:28-45, accounts/forms.py:12-18
- **Detail**: `validate_unique()` is a no-op, and `RegisterView.form_valid` does its own existence check before `save()`. This check-then-save sequence isn't atomic — two concurrent submissions for the same email can both pass the `existing is None` branch, and the second `save()` raises an unhandled `IntegrityError` (500) instead of the intended generic response.
- **Fix**: Wrap `user.save()` in `try/except IntegrityError` and fall back to the "notify existing owner" path on collision.
- **Decision**: FIXED — also applied the same try/except pattern to `complete_email` (F1's fix introduced the identical race there)

### F4 — Link weryfikacyjny to w praktyce 24h magic-login, nie „single-use”

- **Severity**: ⚠️ WARNING
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: Plan Adherence
- **Location**: accounts/views.py:48-62, accounts/tokens.py
- **Detail**: The plan calls this "the signed, single-use-by-expiry verification link", but verification records no consumption state — the token stays valid until expiry (24h) and every hit calls `login(request, user)` again. A leaked link (email-client link scanners, browser history, forwarded mail, proxy logs) grants a working login for up to 24h with no way for the legitimate user to invalidate it early. This is a mismatch with the plan's own wording, not just a general hardening suggestion.
- **Fix A ⭐ Recommended**: After first activation, stop auto-logging-in on repeat clicks — if `user.is_active` is already `True`, redirect to login instead of calling `login()` again.
  - Strength: Removes the magic-login window without breaking the 24h `max_age` contract; a small, local change.
  - Tradeoff: Loses "click and you're already logged in" convenience on a second click of the same link (rare case).
  - Confidence: HIGH — one-line change, doesn't touch `tokens.py`.
  - Blind spot: Haven't confirmed there's no real use case for re-clicking the link while already active.
- **Fix B**: Accept as a deliberate tradeoff; just fix the plan's wording (drop "single-use", keep "time-limited").
  - Strength: Zero code risk.
  - Tradeoff: The 24h replay window stays open.
  - Confidence: MEDIUM — depends how much priority this risk deserves relative to other work.
  - Blind spot: No data on how often verification links actually leak via mail-client scanners in practice.
- **Decision**: FIXED (via Fix A)

### F5 — change.md przestał być aktualizowany po Fazie 1/pauzie w Fazie 2

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Scope Discipline
- **Location**: context/changes/email-registration-auth/change.md
- **Detail**: The `## Notes` section's narrative stops at "Phase 2 status at pause". Two real mid-implementation adaptations from this session never made it in: (1) adding `email=` to ~15 fixtures in `flashcards/tests.py`/`stats/tests.py`, needed because `RequireEmailMiddleware` otherwise treated them as legacy accounts (decided via user prompt this session); (2) adding `pre-commit>=4.6.1` as a dev-dependency in `pyproject.toml`/`uv.lock` during Phase 1, never documented. Earlier phases meticulously documented this kind of discovery — the pattern lapsed.
- **Fix**: Append two paragraphs to `change.md`'s `## Notes` describing both discoveries, matching the existing Phase 1 entries' style.
- **Decision**: FIXED — also added a third Notes paragraph for this review's own findings/fixes

## Observations

### F6 — accounts/urls.py bez app_name, w odróżnieniu od flashcards/stats

- **Severity**: 👁️ OBSERVATION
- **Dimension**: Pattern Consistency
- **Location**: accounts/urls.py
- **Detail**: `flashcards/urls.py` and `stats/urls.py` both declare `app_name` and are namespaced; `accounts/urls.py` doesn't — works today only because no other app collides on names (register, verify_email, resend_verification, complete_email).
- **Fix**: Add `app_name = 'accounts'` and update the ~4 URL names at their call sites, or explicitly document the exception.
- **Decision**: FIXED — namespaced `accounts/urls.py` and updated all `reverse()`/`{% url %}` call sites across views.py, middleware.py, templates, and tests

### F7 — RequireEmailMiddleware liczy reverse() na każdym requeście

- **Severity**: 👁️ OBSERVATION
- **Dimension**: Architecture
- **Location**: accounts/middleware.py:24-26
- **Detail**: The exempt-path set is rebuilt from scratch on every request from any authenticated, emailless legacy user — cheap but avoidable work on a path that by design fires repeatedly for the same users.
- **Fix**: Hoist the exempt-path set to a module-level constant built once.
- **Decision**: FIXED — used a `cached_property` on the middleware instance instead of a bare module-level constant, since `reverse()` needs the URLConf loaded, which isn't guaranteed at import time

### F8 — USERNAME_FIELD/REQUIRED_FIELDS wciąż wskazują na username

- **Severity**: 👁️ OBSERVATION
- **Dimension**: Pattern Consistency
- **Location**: accounts/models.py
- **Detail**: `CustomUser` doesn't override `USERNAME_FIELD`/`REQUIRED_FIELDS` (still `'username'`/`['email']` from `AbstractUser`), even though the rest of the feature treats email as the primary identifier. Not a functional bug (`bootstrap_custom_user` works around it for the initial migration), but conceptually inconsistent with the feature's own intent.
- **Fix**: Optional — consider `USERNAME_FIELD = 'email'` as a separate, deliberate change (affects `createsuperuser` and some admin behavior); not urgent now.
- **Decision**: SKIPPED — user opted to leave this for a separate, deliberate change given its wider blast radius (createsuperuser, admin)