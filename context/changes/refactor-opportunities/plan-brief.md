# K1: Session key typed wrapper — Plan Brief

> Full plan: `context/changes/refactor-opportunities/plan.md`
> Research: `context/changes/refactor-opportunities/research.md`

## What & Why

53 string literals (`"session_topic_id"`, `"session_cards"`, …) are scattered across
`flashcards/views.py` (21) and `flashcards/tests.py` (32) with no single source of
truth. Every new test that sets up session state must know all key names as raw strings;
a typo passes silently. The existing `_SESSION_KEYS` list was a partial attempt at
consolidation — it only covers two cleanup loops. This plan completes that work by
centralising the session contract in a new `flashcards/session.py`.

## Starting Point

`flashcards/views.py:16-22` has `_SESSION_KEYS = [...]` used solely in bulk-pop loops.
Five view functions (`TopicsListView`, `session_start`, `session_results`, `study_review`,
`study_card`) access session keys directly via string literals. 69 tests pass; no CI/CD
exists — Django test suite is the only safety net.

## Desired End State

All session key accesses in `views.py` and `tests.py` use `SK.<CONSTANT>` (writes,
pops, set checks) or `state = get_session(request); state[SK.<KEY>]` (typed reads).
`_SESSION_KEYS` is removed. 69 tests pass. A new `flashcards/session.py` is the single
definition point for all session key names, their types, and the typed read helper.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|----------|--------|------------------|--------|
| Scope | K1 only (session keys) | Strongest candidate; K2 rejected (deliberate design), K3 out of scope | Research |
| Wrapper type | SK constants + TypedDict + `get_session()` | Constants give immediate autocomplete/rename benefit; TypedDict enables mypy when added later | Plan |
| Helper functions | `get_session(request)` only | `clear_session` / `init_session` would add API surface beyond what's needed | Plan |
| `last_wrong_ids` | SK constant only, not in TypedDict | Transient handoff key; not always present — would require `total=False` on an otherwise total TypedDict | Plan |
| Phase granularity | One view per phase (5 phases) | Minimises diff per commit; any failure is immediately localised | Plan |

## Scope

**In scope:**
- New `flashcards/session.py` with `SK` class, `SessionState` TypedDict, `get_session()`
- Migrate all 5 view functions in `flashcards/views.py`
- Migrate all affected test methods in `flashcards/tests.py`
- Remove `_SESSION_KEYS` from `views.py`

**Out of scope:**
- K3 (remove `session_score`)
- K2 (cross-app import boundary)
- `clear_session()` / `init_session()` helpers
- Mypy CI configuration
- Any change to session runtime behaviour or Django session backend

## Architecture / Approach

`flashcards/session.py` is a new module with zero external dependencies (only
`typing` + `django.http`). Views import `SK` and `get_session`; tests import `SK`.
The runtime session dict is unchanged — `SK.CARDS == "session_cards"` at runtime,
so no migration, no data change, no compatibility layer needed.

```
flashcards/session.py          ← new: SK, SessionState, get_session()
  ↑                ↑
views.py       tests.py        ← import SK (writes/checks) + get_session (reads)
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|-------|-----------------|----------|
| 1. Scaffold | `flashcards/session.py` created; zero changes to existing files | Import error if TypedDict syntax is wrong for Python 3.14 |
| 2. TopicsListView | First view migrated + test_visiting_topics_clears_session updated | None — simplest view |
| 3. session_start | 5 write literals replaced with SK | None — writes only, no reads |
| 4. session_results | Reads via get_session(); `_SESSION_KEYS` removed | Cleanup loop removal leaves no reference to _SESSION_KEYS — verify grep |
| 5. study_review + study_card | All remaining literals gone; full cycle verified | study_card is the most complex view; SessionHardeningTests touch many keys |

**Prerequisites:** `flashcards/session.py` does not yet exist — Phase 1 creates it.
**Estimated effort:** ~1 session across 5 incremental commits.

## Open Risks & Assumptions

- No mypy configured — TypedDict checking is IDE-only until mypy is added; the plan doesn't change based on this
- `cast(SessionState, request.session)` is a static promise; if a required-key guard is removed in a future refactor, get_session() could return an incomplete TypedDict silently
- `last_wrong_ids` is outside `SessionState` — if new code needs a typed read of that key, the TypedDict will need `total=False` or a separate key definition

## Success Criteria (Summary)

- `grep -n '"session_' flashcards/views.py flashcards/tests.py` → empty (no bare string literals remain)
- `uv run python manage.py test` → 69/69 pass
- Full spaced-repetition cycle (topics → study → results → study again → results) works end-to-end
