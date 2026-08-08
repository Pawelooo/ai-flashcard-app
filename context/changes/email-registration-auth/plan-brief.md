# Email Registration, Verification, Login & Password Reset — Plan Brief

> Full plan: `context/changes/email-registration-auth/plan.md`

## What & Why

Replace username-based auth with email-based auth: register with email+password, verify via a link before the account works, log in with email+password, and reset a forgotten password by email. This fulfills the PRD's own Access Control statement ("Users log in via email/password") which the current `UserCreationForm`-based flow never actually implemented.

## Starting Point

The app uses Django's default `auth.User` untouched, with `UserCreationForm` (username + password, no email) and an immediate auto-login on registration. No `EMAIL_BACKEND` is configured anywhere. Production on Fly.io already has real registered users — all with a blank `email`, since nothing ever collected one.

## Desired End State

New users register with email+password, get a verification email, click it to activate + auto-login. Login is by email+password with generic (non-enumerating) error messages. Existing accounts keep working via their old username and get a one-time, non-blocking nudge to add an email. Forgotten passwords are recoverable via a standard email reset link.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| User model | Swap `AUTH_USER_MODEL` to `CustomUser` | User explicitly chose this over keeping the default `User` model, despite the added migration risk, after confirming production has real (email-less) accounts. |
| Migration technique | `db_table='auth_user'` + `SeparateDatabaseAndState` | Preserves every existing row/password/PK with zero data copying — far safer than a copy-and-repoint migration on live production data. |
| Existing accounts w/o email | Nudge, don't block | They were already active before this change; retroactively locking them out over a new requirement would be a regression, not a fix. |
| Verification token | `django.core.signing.TimestampSigner`, 24h | No new model/migration needed; standard Django mechanism reusing `SECRET_KEY`. |
| Email provider | Resend via plain SMTP | Free tier, no new Python dependency (plain `EMAIL_BACKEND` SMTP config is enough). |
| Unverified login | Block (`is_active=False`) + distinct message | Reuses Django's built-in `is_active` gate and `confirm_login_allowed` hook instead of inventing new state. |
| Resend abuse protection | Rate-limit 1/min per submitted email (not per IP) | A per-IP limit doesn't stop a multi-IP attacker from email-bombing one victim's inbox. |
| Enumeration protection | Generic messages on both registration-with-existing-email and login-with-wrong-credentials | Standard practice; the existing account gets a heads-up email instead of the requester learning it exists. |
| Password reset | In scope, reusing Django's built-in views | User asked to bundle it — shares the same email/token infrastructure as verification. |
| Email styling | Plain text only for v1 | Explicit must-have/nice-to-have cut agreed during planning; styled HTML is a fast follow, not blocking. |

## Scope

**In scope:**
- Email+password registration with uniqueness enforcement
- Mandatory email verification before first use
- Email+password login with enumeration-safe error messages
- Legacy (pre-change) account migration path that never locks anyone out
- Password reset via email

**Out of scope:**
- OAuth/social login (PRD mentions it as an option, not required now)
- Admin-role questions (roadmap S-03) — untouched
- Styled/HTML transactional emails — plain text for v1
- Resend cooldown UI (timer/progress bar) — server-side rate limit only

## Architecture / Approach

A new `accounts` app owns `CustomUser` (mapped onto the existing `auth_user` table via `db_table` override — no data movement), a custom `EmailOrUsernameBackend` (email first, username fallback for legacy accounts), and the registration/verification/resend/complete-email views. Password reset reuses Django's built-in views unmodified. The existing `django_ratelimit` + `RATELIMIT_FAIL_OPEN` pattern extends to every new auth-adjacent endpoint.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. CustomUser + Email Infra | Swapped user model (data-preserving) + Resend email backend | The one genuinely hard-to-reverse step — must be dry-run against a data copy first |
| 2. Registration + Verification | Email registration, signed verification link, resend flow | Token/email edge cases (expired, tampered, duplicate email) |
| 3. Email Login + Legacy Gate | Email-based login, unverified-account messaging, legacy nudge | Getting `confirm_login_allowed` + backend `is_active` handling right without leaking enumeration signals |
| 4. Password Reset | Django's built-in reset flow wired to the new model/email backend | Low — mostly reusing existing Django machinery |

**Prerequisites:** A Resend account + API key (or equivalent SMTP credentials) available as a Fly secret before Phase 1's manual verification step.
**Estimated effort:** ~4 phases, each independently testable; Phase 1 carries most of the schedule risk due to the production data migration.

## Open Risks & Assumptions

- Assumes the Resend free tier is acceptable for this app's expected volume (small user base per PRD `target_scale`).
- Assumes no other code outside `flashcards`/`stats` references `auth.User` or `auth_user` directly (only `settings.AUTH_USER_MODEL` usages were found) — worth a final grep sweep before merging Phase 1.
- The Phase 1 migration must be rehearsed against a copy of the real production data, not just local dev fixtures with only 2 rows — the actual production row count/shape is still somewhat unknown.

## Success Criteria (Summary)

- A brand-new user can register, verify via email, and land inside the app without any manual intervention.
- No existing user, password, or study-history record is lost or altered by the migration.
- Wrong credentials and "email already registered" never reveal account existence to the requester.
