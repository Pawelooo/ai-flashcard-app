# Spaced Repetition Review — Plan Brief

> Full plan: `context/changes/spaced-repetition-review/plan.md`

## What & Why

Add a "Review missed cards" button to the session results screen (FR-006, nice-to-have). After finishing a regular session, a user can immediately review the cards they got wrong — targeting weak spots while they're still fresh. This satisfies the secondary success criterion in the PRD.

## Starting Point

S-01 is fully implemented: `_SESSION_KEYS`, `study_card`, and `session_results` all exist. No `StudySession` DB model was created — session state lives only in the Django session dict, cleared after results render. `CardReview` records (with `reviewed_at` timestamps) are the only persistent trace of past sessions.

## Desired End State

When a user finishes a session with at least one missed card, a "Powtórz błędne karty" button appears on the results screen. Clicking it starts a new session containing only those wrong cards, flowing through the identical study and results views. If the user had a perfect session, the button is absent.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|---|---|---|
| "Last session" definition | 2-hour time window on `reviewed_at` | No StudySession model exists; time-window accurately approximates a session without a new migration |
| Entry point | Results screen only | Natural highest-motivation moment — user just saw which cards they missed |
| Empty state | Hide button entirely | No dead-end UX when there's nothing to review |
| Session infrastructure | Reuse unchanged | `study_card` + `session_results` work identically; only `study_review` is new |
| `topic_id` for review sessions | `None` (+ template guard) | No topic applies; "Study again" button hidden via `{% if topic_id %}` |
| Leaderboard scoring | Count equally | PRD Business Logic explicitly requires this; no code change needed |
| URL | `/flashcards/study/review/` + `study_review` | Consistent with `/study/start/` and `/study/results/` naming |

## Scope

**In scope:** `study_review` view, URL registration, `timedelta` import, two template edits to `session_results.html`, 5 integration tests.

**Out of scope:** Full SRS algorithm (SM-2/FSRS), `StudySession` DB model, topics page entry point, separate "Review again" button post-review, any new migrations.

## Architecture / Approach

`study_review` is a POST-only view that mirrors `session_start`: query CardReview for wrong cards in the last 2 hours → shuffle → write `_SESSION_KEYS` to Django session → redirect to `flashcards:study`. The study loop and results screen are completely unchanged. Two template edits: (1) wrap "Study again" in `{% if topic_id %}`, (2) add "Powtórz błędne karty" form inside the existing missed-cards block.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. View + URL + templates | Full review flow works end-to-end | `session_topic_id = None` breaking "Study again" — guarded by `{% if topic_id %}` |
| 2. Integration tests | 5 tests covering guards, happy path, template conditionals | None significant |

**Prerequisites:** S-01 (`complete-study-session`) done ✓  
**Estimated effort:** ~1 session across 2 phases

## Open Risks & Assumptions

- The 2-hour window fails if a user pauses mid-session longer than 2 hours — acceptable edge case for MVP.
- A card deleted after a session leaves `card_id = NULL` in CardReview; filtered out via `card__isnull=False`.

## Success Criteria (Summary)

- "Powtórz błędne karty" button appears on results screen when and only when missed cards exist
- Review session contains exactly the wrong cards from the last 2-hour window
- All 5 integration tests pass with no regressions
