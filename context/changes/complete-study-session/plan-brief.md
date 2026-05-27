# Kompletna Sesja Nauki — Plan Brief

> Full plan: `context/changes/complete-study-session/plan.md`

## What & Why

The AI Flashcard App's primary success criterion (PRD, US-01) is that a user can pick a topic, flip through a deck, and receive an accurate score. The current study view serves random cards in an infinite loop with no session boundary — it proves nothing about the product's core value. This plan replaces that loop with a real end-to-end session flow.

## Starting Point

A stateless `study` view at `/flashcards/study/` picks a random card from the full pool on every GET. `CardReview` records are created on POST but never aggregated into a session score. There is no topic selection screen, no deck ordering, and no results page. The `Topic` model is not yet in the database (F-02 prerequisite must be done first).

## Desired End State

A logged-in user lands on `/flashcards/topics/`, selects a topic, and flips through that topic's complete card deck in a shuffled order — one card at a time, with a "Card N of M" progress indicator. After the last card they see a score screen: X/N correct, percentage, list of missed card questions, and buttons to study again or choose a different topic.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|---|---|---|
| Prerequisite scope | Assume F-02 done separately | Keeps each change independently reviewable; matches roadmap ordering |
| Session state storage | Django session dict (`request.session`) | Zero new DB tables; fits the POST-redirect-GET pattern; sufficient for MVP scale |
| Card ordering | Shuffled once per session | Prevents order memorization; trivial with `random.shuffle` |
| Score screen content | Score + % + missed card list + retry + home | Closes the feedback loop; previews S-04 (spaced repetition) without requiring it |
| Home redirect target | New `/flashcards/topics/` route | Keeps `/flashcards/` as the existing card-list admin view; clean URL for topic selection |
| Session abandonment | Always restart (topics visit clears session) | Predictable behavior; avoids confusing mid-session resume states |
| URL structure | Single `/flashcards/study/` URL, state in session | Matches existing view pattern; no URL routing complexity |
| Testing | Full integration tests (Django test client) | Catches template + URL + view bugs; 5 targeted test cases |

## Scope

**In scope:**
- Topic selection page at `/flashcards/topics/`
- Session initialization via POST to `/flashcards/study/start/`
- Session-aware study view with progress indicator
- Score screen at `/flashcards/study/results/` with missed card list
- Update home/register redirects + navbar + stats dashboard CTA to point to topics
- 5 integration tests covering happy path + all guard conditions

**Out of scope:**
- Topic model / Card→Topic FK (F-02, prerequisite)
- StudySession DB model (Django session dict is sufficient)
- Spaced repetition (S-04)
- Leaderboard (S-02)
- Resume of abandoned sessions
- Changes to card-list or card-create views

## Architecture / Approach

State for the in-progress session lives entirely in the Django session dict under five keys (`session_topic_id`, `session_cards`, `session_index`, `session_score`, `session_wrong_ids`). The flow is:

```
GET  /flashcards/topics/         → clear session → show topics
POST /flashcards/study/start/    → shuffle + init session → redirect to /study/
GET  /flashcards/study/          → read session → show card N of M
POST /flashcards/study/          → record CardReview → advance index → redirect
GET  /flashcards/study/results/  → read + clear session → show score screen
```

`CardReview` records created during the session feed the existing `stats/services.py` stats dashboard automatically — no changes needed there.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Topic Selection Entry Point | `/flashcards/topics/` view + template; updated redirects/links | Topics page requires F-02 data to be meaningful |
| 2. Session Initialization + Card Loop | `session_start` + rewritten `study_card`; full deck traversal | Session dict key typos cause silent failures across views |
| 3. Score Screen + Integration Tests | Results view + template; 5 integration tests | Test setup requires Topic + Card fixtures (F-02 models must exist) |

**Prerequisites:** F-02 (Topic model + Card FK + seeded data) implemented and migrated before phase 1 manual verification.

**Estimated effort:** ~1–2 sessions across 3 phases.

## Open Risks & Assumptions

- F-02 is not yet implemented. This plan cannot be manually verified until Topic records exist in the database.
- If a Topic's Card FK is named differently than `topic.cards` (the standard Django reverse relation), the `session_start` queryset call needs adjustment.
- Django session middleware is assumed active (it is in Django's default `MIDDLEWARE` list).

## Success Criteria (Summary)

- A logged-in user can complete the full flow end-to-end: topics → session → results — with no dead ends.
- The score on the results screen accurately reflects the user's actual answers (PRD guardrail: "A wrong score breaks the only feedback loop the app provides").
- All 5 integration tests pass; no regressions in existing tests.
