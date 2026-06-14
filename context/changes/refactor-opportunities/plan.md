# K1: Session key typed wrapper — Implementation Plan

## Overview

Replace 53 string-literal session key accesses (`"session_topic_id"`, `"session_cards"`, …)
scattered across `flashcards/views.py` (21) and `flashcards/tests.py` (32) with typed
constants and a session helper, centralising the session contract in a new module
`flashcards/session.py`.

## Current State Analysis

`flashcards/views.py:16-22` defines `_SESSION_KEYS` — a plain list used only in two
bulk-pop loops: `TopicsListView.get()` (line 32) and `session_results()` (line 80).
All other session accesses (21 in views, 32 in tests) are bare string literals spread
across 5 view functions and 13 test methods. No typed layer exists in `flashcards/`;
the only codebase precedent is `stats/types.py:5-11` (`@dataclass(frozen=True) StudyStats`).

A sixth session key, `last_wrong_ids`, is NOT in `_SESSION_KEYS`. It is a transient
handoff key written in `session_results()` (line 79) and popped in `study_review()` (line 150).

## Desired End State

Every session key access in `flashcards/views.py` and `flashcards/tests.py` uses
`SK.<CONSTANT>` (writes, pops, set checks) or `state = get_session(request); state[SK.<KEY>]`
(typed reads). `_SESSION_KEYS` is removed from `views.py`. All 69 tests pass unchanged
in behaviour.

### Key Discoveries

- `_SESSION_KEYS` referenced in exactly 2 cleanup loops; underutilised as consolidation
  mechanism — evidence (`flashcards/views.py:32-33`, `80-81`)
- `last_wrong_ids` is absent from `_SESSION_KEYS`; only 2 accesses
  (`views.py:79` write, `views.py:150` pop) — evidence
- `stats/types.py:5-11` is the only typed-data precedent — evidence
- No mypy configured; TypedDict value = IDE autocomplete + future-proofing — inference
- `get_session()` uses `cast(SessionState, request.session)` — safe because all call
  sites are guarded by the required-key check that fires before get_session() — inference

## What We're NOT Doing

- K3 (eliminate `session_score`): separate change, out of scope
- K2 (cross-app import): rejected in research, out of scope
- `clear_session()` or `init_session()` helpers — only `get_session()` is added
- Including `last_wrong_ids` in `SessionState` TypedDict — it is a transient handoff key,
  not part of the stable 5-key session contract
- Configuring mypy CI — the typed wrapper is ready for it but does not require it

## Implementation Approach

Scaffold first (`flashcards/session.py`, Phase 1 — zero changes to existing files),
then migrate one view function per phase (Phases 2–5). Each phase updates the view
and the tests whose string literals belong to that view's session interactions.
`_SESSION_KEYS` definition stays in `views.py` until Phase 4 removes its last reference.

## Critical Implementation Details

**`last_wrong_ids` scope**: `SK.LAST_WRONG_IDS = "last_wrong_ids"` is a constant in
`SK` but intentionally absent from `SessionState`. Access via
`request.session.pop(SK.LAST_WRONG_IDS, None)` directly — do not go through `get_session()`.

**TypedDict and `cast`**: `get_session()` calls `cast(SessionState, request.session)`.
Django's `SessionBase` keys are typed as `Any`; the cast is a static promise, not a
runtime check. It is safe because every call site is downstream of a required-key guard.

**SK constants and set membership**: `{SK.CARDS, SK.INDEX, ...}` in required-set checks
works at runtime because `SK.CARDS == "session_cards"` — the string values are unchanged;
only the access pattern changes.

---

## Phase 1: Scaffold `flashcards/session.py`

### Overview

Create the new module. Zero changes to any existing file. Establishes the contract
that all later phases import.

### Changes Required

#### 1. New module `flashcards/session.py`

**File**: `flashcards/session.py` (new)

**Intent**: Single source of truth for session key names, their types, and the typed
read helper. Nothing else imports it yet.

**Contract**:

```python
from typing import TypedDict, cast
from django.http import HttpRequest


class SK:
    TOPIC_ID = "session_topic_id"
    CARDS = "session_cards"
    INDEX = "session_index"
    SCORE = "session_score"
    WRONG_IDS = "session_wrong_ids"
    LAST_WRONG_IDS = "last_wrong_ids"
    ALL = [TOPIC_ID, CARDS, INDEX, SCORE, WRONG_IDS]


class SessionState(TypedDict):
    session_topic_id: int | None
    session_cards: list[int]
    session_index: int
    session_score: int
    session_wrong_ids: list[int]


def get_session(request: HttpRequest) -> SessionState:
    return cast(SessionState, request.session)
```

`SK.ALL` mirrors `_SESSION_KEYS` order (topic_id, cards, index, score, wrong_ids).

### Success Criteria

#### Automated Verification

- Module importable: `uv run python -c "from flashcards.session import SK, SessionState, get_session; print('ok')"`
- No regressions — full suite passes without any import change in views: `uv run python manage.py test`

---

## Phase 2: Migrate `TopicsListView`

### Overview

Add the import to `views.py`. Replace `_SESSION_KEYS` in the cleanup loop with `SK.ALL`.
Update the one test that directly asserts on session key names.

### Changes Required

#### 1. `flashcards/views.py` — import + TopicsListView.get()

**File**: `flashcards/views.py`

**Intent**: Wire the import; replace the loop reference. `_SESSION_KEYS` definition stays
(still used by `session_results`).

**Contract**: Add `from flashcards.session import SK, get_session` to the imports block.
In `TopicsListView.get()` (line 32): `for key in _SESSION_KEYS:` → `for key in SK.ALL:`.

#### 2. `flashcards/tests.py` — test_visiting_topics_clears_session

**File**: `flashcards/tests.py`

**Intent**: Replace the 10 string literals (5 setup assignments + 5 `assertNotIn` calls)
in the test that directly verifies session cleanup.

**Contract**: Add `from flashcards.session import SK` to the imports block. In
`test_visiting_topics_clears_session` (lines 80-93): replace every
`session['session_*']` key and `assertNotIn('session_*', ...)` argument with the
corresponding `SK.*` constant.

### Success Criteria

#### Automated Verification

- Full suite passes: `uv run python manage.py test`

#### Manual Verification

- Visit `/flashcards/topics/` while logged in with an active session → session keys are cleared

**Implementation Note**: Pause after automated verification passes; confirm manual step
before proceeding to Phase 3.

---

## Phase 3: Migrate `session_start`

### Overview

Replace the 5 inline string literal writes in `session_start()` with SK constants.
No test changes needed — tests for session_start call the view and don't manually set keys.

### Changes Required

#### 1. `flashcards/views.py` — session_start writes

**File**: `flashcards/views.py`

**Intent**: The 5 `request.session['...'] = ...` assignments (lines 50-54) become
SK-keyed. Behaviour is identical; string values at runtime are unchanged.

**Contract**: Lines 50-54 — replace each string key:
`'session_topic_id'` → `SK.TOPIC_ID`, `'session_cards'` → `SK.CARDS`,
`'session_index'` → `SK.INDEX`, `'session_score'` → `SK.SCORE`,
`'session_wrong_ids'` → `SK.WRONG_IDS`.

### Success Criteria

#### Automated Verification

- Full suite passes: `uv run python manage.py test`

#### Manual Verification

- Start a study session from the topics page → study card renders with the first card

**Implementation Note**: Pause after automated verification; confirm manual step before Phase 4.

---

## Phase 4: Migrate `session_results`

### Overview

Three patterns in `session_results()` become SK-based: required-set check, four reads
(via `get_session()`), and cleanup loop. Remove `_SESSION_KEYS` from `views.py` after its
last reference is replaced. Update affected tests.

### Changes Required

#### 1. `flashcards/views.py` — session_results + remove `_SESSION_KEYS`

**File**: `flashcards/views.py`

**Intent**: Migrate all session accesses in `session_results()` to SK. Once done,
`_SESSION_KEYS` has zero references and must be removed.

**Contract**:
- Required set (line 60): `{'session_cards', 'session_score', 'session_wrong_ids', 'session_topic_id'}` → `{SK.CARDS, SK.SCORE, SK.WRONG_IDS, SK.TOPIC_ID}`
- Reads (lines 64-67): insert `state = get_session(request)` before the four reads; replace each `request.session['...']` read with `state[SK.<KEY>]`
- Handoff write (line 79): `request.session['last_wrong_ids']` → `request.session[SK.LAST_WRONG_IDS]`
- Cleanup loop (line 80): `for key in _SESSION_KEYS:` → `for key in SK.ALL:`
- Remove `_SESSION_KEYS = [...]` definition from views.py (lines 16-22)

#### 2. `flashcards/tests.py` — session_results tests

**File**: `flashcards/tests.py`

**Intent**: Update setup blocks and assertions in tests that manually populate the
session for `session_results` scenarios.

**Contract**:
- `test_session_results_partial_keys_redirects` (lines 392-397): replace `session['session_cards']`, `session['session_score']`, `session['session_wrong_ids']` with SK constants
- `test_full_session_happy_path` (line 54): `'session_cards'` → `SK.CARDS` in `assertNotIn`

### Success Criteria

#### Automated Verification

- Full suite passes: `uv run python manage.py test`
- `_SESSION_KEYS` removed: `grep -rn "_SESSION_KEYS" flashcards/` → no output

#### Manual Verification

- Complete a study session → results page renders correctly with score, total, and missed card list

**Implementation Note**: Pause after automated verification; confirm manual step before Phase 5.

---

## Phase 5: Migrate `study_review` + `study_card`

### Overview

Migrate the two remaining views and the bulk of remaining test string literals
(SessionHardeningTests and SpacedRepetitionTests). After this phase, no bare session
key string literals remain in `views.py` or `tests.py`.

### Changes Required

#### 1. `flashcards/views.py` — study_review

**File**: `flashcards/views.py`

**Intent**: Replace `'last_wrong_ids'` pop and 5 session key writes with SK constants.

**Contract**: Line 150: `request.session.pop('last_wrong_ids', None)` → `request.session.pop(SK.LAST_WRONG_IDS, None)`. Lines 157-161: same pattern as Phase 3 — replace each write key with SK.TOPIC_ID, SK.CARDS, SK.INDEX, SK.SCORE, SK.WRONG_IDS.

#### 2. `flashcards/views.py` — study_card

**File**: `flashcards/views.py`

**Intent**: Replace required-set literals with SK constants; use `get_session()` for the four reads; replace the two writes with SK constants.

**Contract**:
- Required set (line 167): `{'session_cards', 'session_index', 'session_score', 'session_wrong_ids'}` → `{SK.CARDS, SK.INDEX, SK.SCORE, SK.WRONG_IDS}`
- Reads (lines 171-172): insert `state = get_session(request)` before reads; `request.session['session_cards']` → `state[SK.CARDS]`, `request.session['session_index']` → `state[SK.INDEX]`
- Writes (lines 187-193): `request.session['session_score']` → `request.session[SK.SCORE]`, `request.session['session_wrong_ids']` → `request.session[SK.WRONG_IDS]`, `request.session['session_index']` → `request.session[SK.INDEX]`

#### 3. `flashcards/tests.py` — SpacedRepetitionTests + SessionHardeningTests

**File**: `flashcards/tests.py`

**Intent**: Replace all remaining string literal session key accesses in test setup blocks and assertions.

**Contract**:
- SpacedRepetitionTests (lines 129, 134, 157-161, 236): replace string keys for `last_wrong_ids`, `session_cards`, `session_score`, `session_wrong_ids`, `session_topic_id`, `session_index` with SK constants
- SessionHardeningTests (lines 342, 348-356, 361, 369-371, 383-386): replace all remaining string literal session key accesses in setup assignments and `self.client.session[...]` assertions

### Success Criteria

#### Automated Verification

- Full suite passes: `uv run python manage.py test`
- No bare string session key literals remain in views or tests: `grep -n '"session_' flashcards/views.py flashcards/tests.py` → empty (or only non-session-key strings unrelated to this refactor)
- Module import verified: `uv run python -c "from flashcards.session import SK, get_session, SessionState; print('ok')"`

#### Manual Verification

- Complete a full spaced-repetition cycle: topics → start session → answer all cards → results → click "Study Again" → answer review cards → review results

**Implementation Note**: After automated verification passes and manual cycle is confirmed, the refactor is complete.

---

## Testing Strategy

### Unit Tests

No new tests required. The refactor is purely structural — runtime behaviour and session
dict key strings are unchanged. The existing 69 tests cover all session state transitions.

### Integration Tests

Full suite (`uv run python manage.py test`) runs at the end of every phase. A failing
test after a single-view migration is immediately localised to that view's diff.

### Manual Testing Steps

1. Log in → visit topics → confirm active session is cleared
2. Select topic → start session → answer all cards (mix correct/incorrect) → verify results page
3. Click "Study Again" → answer review deck → verify review results page
4. Visit topics mid-session → confirm redirect and session clear

---

## Performance Considerations

None. `SK` class attributes are string constants (O(1) lookup). `get_session()` is a
single `cast()` call with zero runtime overhead — no dict copying or object construction.

---

## References

- Research: `context/changes/refactor-opportunities/research.md`
- Source report: `context/changes/complete-study-session/research.md`
- Pattern precedent: `stats/types.py:5-11`
- Existing scaffold: `flashcards/views.py:16-22` (`_SESSION_KEYS`)
- Views under migration: `flashcards/views.py:25-206`
- Tests under migration: `flashcards/tests.py:1-579`

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Scaffold flashcards/session.py

#### Automated

- [x] 1.1 Module importable: `uv run python -c "from flashcards.session import SK, SessionState, get_session; print('ok')"`
- [x] 1.2 Full suite passes unchanged: `uv run python manage.py test`

### Phase 2: Migrate TopicsListView

#### Automated

- [ ] 2.1 Full suite passes: `uv run python manage.py test`

#### Manual

- [ ] 2.2 Visit /flashcards/topics/ with active session → session cleared

### Phase 3: Migrate session_start

#### Automated

- [ ] 3.1 Full suite passes: `uv run python manage.py test`

#### Manual

- [ ] 3.2 Start a study session → study card renders with first card

### Phase 4: Migrate session_results

#### Automated

- [ ] 4.1 Full suite passes: `uv run python manage.py test`
- [ ] 4.2 _SESSION_KEYS removed: `grep -rn "_SESSION_KEYS" flashcards/` → no output

#### Manual

- [ ] 4.3 Complete a study session → results page renders correctly

### Phase 5: Migrate study_review + study_card

#### Automated

- [ ] 5.1 Full suite passes: `uv run python manage.py test`
- [ ] 5.2 No bare string session key literals remain: `grep -n '"session_' flashcards/views.py flashcards/tests.py` → empty
- [ ] 5.3 Module import verified: `uv run python -c "from flashcards.session import SK, get_session, SessionState; print('ok')"`

#### Manual

- [ ] 5.4 Complete full spaced-repetition cycle: topics → start → study → results → study again → results
