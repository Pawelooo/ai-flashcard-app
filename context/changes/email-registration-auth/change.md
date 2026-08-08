---
change_id: email-registration-auth
title: Email-based registration, verification, login, and password reset
status: implementing
created: 2026-07-27
updated: 2026-07-28
archived_at: null
---

## Notes

- Confirmed during planning: Fly.io production has real registered users, all with blank `email` (current registration only ever collected `username`). This ruled out a destructive reset and drove the data-preserving `AUTH_USER_MODEL` migration approach in Phase 1.
- Scope grew from "register + verify + login" to include password reset — user explicitly asked to bundle it since it shares the same email/token infrastructure.
- Plan review (2026-07-28, see `reviews/plan-review.md`): found and fixed 3 critical gaps in the plan before implementation — (1) new email-only registrations would collide on `username=''` after the second signup, fixed by making `username` nullable via the same blank→NULL pattern used for `email`; (2) `flashcards/tests.py` and `verify_manual_checks.py` import the concrete (soon-to-be-swapped) `auth.models.User` directly, which would break `manage.py test`; (3) no `accounts/admin.py` was planned, which would have broken the admin's Users page (used for content seeding) after the `AUTH_USER_MODEL` swap. Two lower-priority items (nav/leaderboard `username` display, missing e2e coverage for registration) were accepted as risks for implementation time.
