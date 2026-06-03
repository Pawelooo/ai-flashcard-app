# Score Accuracy & Session Hardening — Integration Tests

## Overview

Add `SessionHardeningTests` class to `flashcards/tests.py` with 7 integration tests and one view fix covering three risks from `context/foundation/test-plan.md §2`: score-counter divergence from DB (Risk #1), unauthorized cross-card POST (Risk #2), and partial session state causing `KeyError → 500` (Risk #3).

## Current State Analysis

S-01 (`complete-study-session`) is fully implemented and `impl_reviewed`. The existing `StudySessionTests` (5 tests) covers the happy path, empty-deck guard, missing-session guards, and session reset — but none of those tests independently verify `CardReview` row counts against `session_score`, exercise the cross-card guard, or simulate partial session state.

Current code facts (source: `context/changes/complete-study-session/research.md`):
- `session_score` (Django session, ephemeral) and `CardReview.is_correct` (PostgreSQL, durable) are two independent state stores; PRD guardrail requires them to always agree
- Guard at `views.py:130` (`card_id != card_ids[index]`) fires BEFORE `CardReview.objects.create()` at line 134 — architecture is correct, but there is no regression test
- `study_card` reads `session_index` (line 123) and increments `session_score` (line 136) via plain dict access with no `KeyError` protection — a single absent key causes `500`

## Desired End State

After this plan:
1. `uv run python manage.py test flashcards` passes with 7 new tests in `SessionHardeningTests` alongside all 12 existing tests
2. Any regression that diverges `session_score` from `CardReview` counts, removes/reorders the cross-card guard, or reverts the partial-session fix is caught immediately
3. `study_card` handles any partial session state with a clean redirect (not `500`), using the same `required.issubset()` pattern as `session_results`

### Key Discoveries

- `context/changes/complete-study-session/research.md §6` — full map of 11 uncovered code paths
- `flashcards/views.py:119-124` — current single-key guard covers only `session_cards`; lines 123 and 136 raise `KeyError` for any other absent key
- `flashcards/views.py:130` — cross-card guard fires before `CardReview.objects.create()` at line 134; ordering is the invariant under protection
- `flashcards/views.py:56-60` — `session_results` already uses `required.issubset(request.session.keys())` — the identical pattern to apply in `study_card`
- `flashcards/tests.py:11-95` — `StudySessionTests` is the fixture template; `SessionHardeningTests` follows the same structure

## What We're NOT Doing

- No template, URL, or model changes
- No new migrations
- No tests for `SpacedRepetitionTests` scenarios (out of scope for this rollout phase)
- No concurrent-tab edge case (documented out-of-MVP-scope in research)
- No auth-boundary tests (test-plan Phase 2)
- No leaderboard tests (test-plan Phase 3)

## Implementation Approach

All 7 tests go in a new `SessionHardeningTests` class in `flashcards/tests.py`. Phases are ordered by impact and dependency: score accuracy first (highest PRD relevance, no view change needed), injection guard second (no view change needed), partial session last (requires a view fix — write tests first, see 2 fail, fix, confirm all green).

## Critical Implementation Details

**Phase 3 ordering is intentional TDD**: write all 4 Risk #3 tests before touching `views.py`. Run the suite — `test_partial_session_missing_index_gets_redirect_not_500` and `test_partial_session_missing_score_post_gets_redirect_not_500` will fail with `KeyError`. This failure is the signal that the bug is real and the tests are correctly wired. Apply the guard fix only after seeing the failures; run again to confirm all 4 pass.

**Guard scope in `study_card`**: the fix must cover `session_score` and `session_wrong_ids` in addition to `session_cards` and `session_index`. The guard fires before `if request.method == 'POST'`, protecting both GET and POST paths with a single check.

---

## Phase 1: Score Accuracy Tests (Risk #1)

### Overview

Add two tests that verify `session_score` agrees with the database independently. After this phase, any code path that diverges the two state stores will cause the suite to fail.

### Changes Required

#### 1. SessionHardeningTests class and setUp

**File**: `flashcards/tests.py`

**Intent**: Create the `SessionHardeningTests(TestCase)` class with a `setUp` and `_start_session` helper, following the `StudySessionTests` pattern identically.

**Contract**: `setUp` creates one `User`, one `Topic` (`name='Hardening Topic', slug='hardening-topic'`), and three `Card` objects. `_start_session()` POSTs to `reverse('flashcards:study_start')` with `{'topic_id': self.topic.pk}`.

#### 2. test_session_score_matches_cardreview_db

**File**: `flashcards/tests.py`

**Intent**: Prove that after a full session with mixed answers, the `CardReview` records in the database independently agree with the score in the results context. Oracle: PRD guardrail "score must reflect actual answers" + Business Logic "session score = count of cards marked correct."

**Contract**: `force_login`; `_start_session()`; loop GET → POST for 3 cards with `is_correct` values `['1', '0', '1']` (2 correct, 1 incorrect); GET `reverse('flashcards:study_results')`. Assert all four independently:
- `response.context['score'] == 2`
- `CardReview.objects.count() == 3`
- `CardReview.objects.filter(is_correct=True).count() == 2`
- `CardReview.objects.filter(is_correct=False).count() == 1`

The `CardReview` assertions must not reference `session_score` — they are the independent oracle.

#### 3. test_missing_is_correct_field_counts_as_incorrect

**File**: `flashcards/tests.py`

**Intent**: Document and protect the behavior that a POST to `/study/` without the `is_correct` field is treated as an incorrect answer (not a crash or skip). Oracle: `views.py:132` semantics — `request.POST.get('is_correct') == '1'` evaluates `None == '1'` → `False`.

**Contract**: `force_login`; `_start_session()`; GET `/study/` to obtain `card_id` from `response.context['card'].pk`; POST `/study/` with only `{'card_id': card_id}` (no `is_correct`). Assert: response is 302; `CardReview.objects.last().is_correct == False`; `self.client.session['session_score'] == 0`.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards.tests.SessionHardeningTests` passes: both new tests green, no regressions in `StudySessionTests` or `SpacedRepetitionTests`

#### Manual Verification

- Code review: `test_session_score_matches_cardreview_db` assertions read from `CardReview.objects.filter()` — they do NOT read `session_score` from the session to build the expected value
- Code review: `test_missing_is_correct_field_counts_as_incorrect` POSTs with a dict that has no `is_correct` key — not `{'is_correct': ''}` or `{'is_correct': '0'}`

---

## Phase 2: Injection Guard Test (Risk #2)

### Overview

Add one test that verifies the cross-card guard both redirects and prevents the database write. This is a regression guard: if someone reorders the POST handler so `CardReview.objects.create()` runs before the index check, the assertion `CardReview.objects.count() == 0` will fail.

### Changes Required

#### 1. test_cross_card_post_rejected_no_db_write

**File**: `flashcards/tests.py`

**Intent**: Prove that POSTing a valid `card_id` at the wrong session index neither advances the session nor creates a `CardReview`. The guard-before-write ordering at `views.py:130 → 134` is the invariant under protection.

**Contract**: `force_login`; `_start_session()`; read `wrong_card_id = self.client.session['session_cards'][1]` (the second card in the shuffled deck, while current index is 0); POST `/study/` with `{'card_id': wrong_card_id, 'is_correct': '1'}`. Assert: response is 302; `CardReview.objects.count() == 0`; `self.client.session['session_score'] == 0`; `self.client.session['session_index'] == 0`.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards.tests.SessionHardeningTests.test_cross_card_post_rejected_no_db_write` passes

#### Manual Verification

- Code review: the test reads `session_cards[1]` (not `session_cards[0]`) — using the correct card PK would test the happy path, not the guard

---

## Phase 3: Partial Session Fix + Tests (Risk #3)

### Overview

Expand the session guard in `study_card` from a single-key check to a comprehensive required-keys check, then add 4 tests verifying the corrected behavior. Two of the 4 tests will fail until the view fix is applied — that failure is intentional and confirms the bug is real.

### Changes Required

#### 1. Expand session guard in study_card

**File**: `flashcards/views.py`

**Intent**: Replace the single-key `'session_cards' not in request.session` guard with a comprehensive subset check covering all four keys that `study_card` reads, preventing `KeyError → 500` for any partial session state.

**Contract**: At `views.py:119-120`, replace the current check with the `required.issubset()` pattern already used in `session_results` at `views.py:58-60`. The `required` set must include `'session_cards'`, `'session_index'`, `'session_score'`, and `'session_wrong_ids'`. Redirect target remains `'flashcards:topics'`.

#### 2. test_partial_session_missing_index_gets_redirect_not_500

**File**: `flashcards/tests.py`

**Intent**: Prove that GET `/study/` with only `session_cards` set (missing `session_index`) produces a redirect, not a `500`. This is the primary `KeyError` risk identified in research (`views.py:123`).

**Contract**: `force_login`; manually set session with only `session_cards = [self.cards[0].pk]` (no other keys); GET `/flashcards/study/`. Assert: `response.status_code == 302`. **Fails on current code before view fix.**

#### 3. test_partial_session_missing_score_post_gets_redirect_not_500

**File**: `flashcards/tests.py`

**Intent**: Prove that POST `/study/` with `session_cards` and `session_index` present but `session_score` absent produces a redirect with no database write, not a `KeyError` at `views.py:136` (`session_score += 1`).

**Contract**: `force_login`; set session: `session_cards=[self.cards[0].pk]`, `session_index=0`, `session_wrong_ids=[]` (no `session_score`); POST `/flashcards/study/` with `{'card_id': self.cards[0].pk, 'is_correct': '1'}`. Assert: `response.status_code == 302`; `CardReview.objects.count() == 0` (guard fires before write). **Fails on current code before view fix.**

#### 4. test_session_index_out_of_bounds_get_redirects_to_results

**File**: `flashcards/tests.py`

**Intent**: Verify the bounds-check guard at `views.py:149` redirects to results rather than raising `IndexError`. This guard already exists; this test is a regression guard for it.

**Contract**: `force_login`; set session: `session_cards=[self.cards[0].pk]`, `session_index=1` (== `len(session_cards)`, one past the end), `session_score=0`, `session_wrong_ids=[]`; GET `/flashcards/study/`. Assert: `response.status_code == 302`; redirect location contains `'study/results'`.

#### 5. test_session_results_partial_keys_redirects

**File**: `flashcards/tests.py`

**Intent**: Verify the `session_results` guard at `views.py:58-60` redirects cleanly when 3 of 4 required keys are present. This guard already exists; this test is a regression guard for it.

**Contract**: `force_login`; set session: `session_cards=[self.cards[0].pk]`, `session_score=1`, `session_wrong_ids=[]` (missing `session_topic_id`); GET `/flashcards/study/results/`. Assert: `response.status_code == 302`; redirect location contains `'topics'`.

### Success Criteria

#### Automated Verification

- Add 4 tests, run suite before view fix: `test_partial_session_missing_index_gets_redirect_not_500` and `test_partial_session_missing_score_post_gets_redirect_not_500` fail (confirms bug)
- Apply `study_card` guard fix; run `uv run python manage.py test flashcards` — all 19 tests (12 existing + 7 new) pass

#### Manual Verification

- Code review: expanded guard in `study_card` uses `required.issubset(request.session.keys())` — same idiom as `session_results:58-60`, no new pattern introduced
- Code review: `test_partial_session_missing_score_post_gets_redirect_not_500` asserts `CardReview.objects.count() == 0`, proving the guard fires before any DB write

---

## Testing Strategy

### Integration Tests

7 integration tests, each asserting at least two independent properties (response code + DB state, or session state + DB state). No unit tests needed — all behavior is at the view layer and requires the Django test client to exercise.

### Manual Testing Steps

1. Run `uv run python manage.py test flashcards` — all 12 existing tests pass before starting
2. Add `SessionHardeningTests` class with Phase 1 tests (2 tests) → run → 2 new tests pass
3. Add Phase 2 test (1 test) → run → 3 new tests pass
4. Add Phase 3 tests only (4 tests, no view fix yet) → run → 2 tests fail (missing_index and missing_score); confirm failure message mentions `KeyError`
5. Apply view fix to `study_card` → run → all 7 new tests pass, 0 regressions

## Performance Considerations

Phase 3 adds one `issubset()` check per request to `study_card` — negligible overhead at any expected scale.

## References

- Oracle: `context/changes/complete-study-session/research.md §6 Luki testowe`
- Risk map: `context/foundation/test-plan.md §2`
- View under test: `flashcards/views.py:117-156` (`study_card`)
- Existing guard pattern: `flashcards/views.py:56-60` (`session_results`)
- Existing test pattern: `flashcards/tests.py:11-95` (`StudySessionTests`)

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Score Accuracy Tests (Risk #1)

#### Automated

- [x] 1.1 `uv run python manage.py test flashcards.tests.SessionHardeningTests` passes (both new tests green, no regressions) — 83622f0

#### Manual

- [x] 1.2 Code review: score test reads from CardReview DB counts, not from session_score — 83622f0
- [x] 1.3 Code review: missing_is_correct test sends POST without is_correct key (not empty string) — 83622f0

### Phase 2: Injection Guard Test (Risk #2)

#### Automated

- [x] 2.1 `uv run python manage.py test flashcards.tests.SessionHardeningTests.test_cross_card_post_rejected_no_db_write` passes — 22673f8

#### Manual

- [x] 2.2 Code review: test uses session_cards[1] (not session_cards[0]) as the wrong-index card ID — 22673f8

### Phase 3: Partial Session Fix + Tests (Risk #3)

#### Automated

- [x] 3.1 4 Phase 3 tests added before view fix: missing_index and missing_score tests fail with KeyError
- [x] 3.2 View fix applied; `uv run python manage.py test flashcards` — all 20 tests pass

#### Manual

- [x] 3.3 Code review: expanded guard in study_card uses required.issubset() matching session_results pattern
- [x] 3.4 Code review: test_partial_session_missing_score_post asserts CardReview.objects.count() == 0
