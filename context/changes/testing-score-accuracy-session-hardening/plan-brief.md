# Score Accuracy & Session Hardening — Plan Brief

> Full plan: `context/changes/testing-score-accuracy-session-hardening/plan.md`
> Research: `context/changes/complete-study-session/research.md`

## What & Why

Add 7 integration tests and one view fix to prove three risks from `test-plan.md §2` are protected. The PRD guardrail ("a wrong score breaks the only feedback loop the app provides") is currently unverifiable — no test independently checks that `session_score` matches the `CardReview` database count. The cross-card POST guard exists but has no regression test, and partial session state causes `KeyError → 500`.

## Starting Point

`StudySessionTests` (5 tests) covers happy path and missing-session guards, but none of its tests read `CardReview.objects.count()`. `study_card` has a single-key guard covering only `session_cards` — any other absent key (e.g., `session_index`) hits an unhandled dict access and crashes. The cross-card guard at `views.py:130` has never been exercised by a test.

## Desired End State

After this plan, any regression that (a) diverges `session_score` from `CardReview` counts, (b) removes or reorders the cross-card guard, or (c) breaks partial-session handling will cause the test suite to fail. `study_card` will handle partial session state with a redirect, not a 500.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| Test location | New class `SessionHardeningTests` in `flashcards/tests.py` | Consistent with existing pattern; Django auto-discovers | Plan |
| Risk #1 approach | New test alongside happy-path, not modifying it | Preserves existing tests; new test has independent oracle | Plan |
| Risk #2 depth | Redirect + `CardReview.count() == 0` | Proves both the guard AND no DB side effect in one test | Plan |
| Risk #3 scope | All 4 variants from research | 4 independent code paths, each with different KeyError source | Plan (user) |
| is_correct variants | Missing field only | Most realistic; all non-`'1'` values share identical semantics | Plan (user) |
| Phase 3 ordering | Write tests first, see 2 fail, then fix view | TDD signal confirms bug is real before applying the fix | Plan |

## Scope

**In scope:**
- `SessionHardeningTests`: 7 new integration tests in `flashcards/tests.py`
- 1 view fix: expand `study_card` session guard (single-key → comprehensive `required.issubset()`)
- Risks #1 (score accuracy), #2 (injection guard), #3 (partial session) from test-plan Phase 1

**Out of scope:**
- Auth-boundary tests (test-plan Phase 2)
- Leaderboard tests (test-plan Phase 3)
- Template, URL, or model changes
- Concurrent-tab race condition (out-of-MVP-scope per research)

## Architecture / Approach

All tests use Django `TestCase` + `TestClient` (same as `StudySessionTests`). Partial-session tests manipulate `self.client.session` directly — the same pattern as `test_visiting_topics_clears_session`. The view fix is a one-line pattern change at `views.py:119-120`, replacing the existing single-key check with `required.issubset(request.session.keys())` — the identical guard already used in `session_results:58-60`.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Score accuracy | 2 tests: CardReview count oracle + missing is_correct | Score assertions might accidentally read session_score — review catches this |
| 2. Injection guard | 1 test: cross-card POST blocked before DB write | Wrong card_id chosen for the test would silently test the happy path |
| 3. Partial session | 4 tests + view fix | 2 tests fail before fix — that's expected; fix and green in same phase |

**Prerequisites:** S-01 (`complete-study-session`) fully implemented and tests passing  
**Estimated effort:** ~1 session across 3 phases

## Open Risks & Assumptions

- Phase 3 exposes a real bug in `study_card` — the fix is a one-line guard expansion, but tests must be written before the fix to preserve the TDD signal
- `self.client.session` direct manipulation works as in `test_visiting_topics_clears_session` — confirmed compatible with current Django version

## Success Criteria (Summary)

- All 19 tests pass (`uv run python manage.py test flashcards`): 12 existing + 7 new
- Phase 3 TDD signal observed: 2 tests fail before fix, all 4 pass after fix
- Code review confirms score test reads from `CardReview.objects.filter()`, not from `session_score`
