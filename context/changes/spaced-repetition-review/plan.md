
# Spaced Repetition Review — Implementation Plan

## Overview

Add a "Review missed cards" entry point on the session results screen. Clicking it starts a new study session seeded only from the wrong cards in the user's most recent session (identified via a 2-hour time window on `CardReview.reviewed_at`). The review session reuses the existing session infrastructure — `_SESSION_KEYS`, `study_card`, and `session_results` are unchanged. The only new code is a single `study_review` view, a URL registration, and two small template changes.

Assumes S-01 (`complete-study-session`) is fully implemented before this plan executes.

## Current State Analysis

-   `CardReview` has `user`, `card` (FK, `SET_NULL`), `is_correct`, `reviewed_at`. A time-window query on `reviewed_at` reconstructs last-session wrong cards without a `StudySession` model.
-   `_SESSION_KEYS`, `session_start`, `study_card`, `session_results` are all in `flashcards/views.py` and fully reusable.
-   `session_results.html` always renders the "Study again" button via `{{ topic_id }}`. For a review session `topic_id` will be `None` — the button must be conditionally hidden, otherwise it submits a broken `topic_id=None` to `session_start`.
-   `CardReview.card` is `SET_NULL` — deleted cards leave `card_id = NULL`. The query must filter `card__isnull=False`.
-   `Meta.indexes = [Index(fields=['user', 'reviewed_at'])]` on `CardReview` supports both the `latest()` lookup and the range-filter query used in `study_review`.

## Desired End State

After a study session with at least one missed card, a "Powtórz błędne karty" button appears on the results screen. Clicking it starts a session containing only those wrong cards, flowing through the same `study_card` view and ending at the same `session_results` screen. If the user has no wrong cards or no session history, the button is absent.

### Key Discoveries

-   `session_topic_id = None` for review sessions — `session_results` reads this and passes it to the template as `topic_id`. The `{% if topic_id %}` guard on "Study again" is required; without it `get_object_or_404(Topic, pk=None)` raises Http404.
-   `study_review` mirrors `session_start` exactly — only the card-ID source differs (DB query vs topic FK).
-   `from datetime import timedelta` is not yet imported in `flashcards/views.py` — must be added.

## What We're NOT Doing

-   No `StudySession` DB model — session boundaries are inferred from the 2-hour time window.
-   No full SRS algorithm (SM-2, FSRS) — v1 is "wrong cards from last session" only.
-   No review entry point on the topics page — results screen only.
-   No separate "Study again" button for review sessions (the existing "Wybierz temat" button is the exit path).
-   No special leaderboard handling — review session `CardReview` records count equally per PRD Business Logic.

## Implementation Approach

Phase 1 adds the `study_review` view, URL, and two template edits (guard on "Study again" + new "Review" button). After Phase 1 the full flow is manually testable end-to-end. Phase 2 adds the test suite.

## Critical Implementation Details

**`session_topic_id = None` for review sessions** — `session_results` passes this directly to the template. The `{% if topic_id %}` guard on "Study again" is required. Without it, the form POSTs `topic_id=None`, and `get_object_or_404(Topic, pk=None)` raises Http404.

**Deleted-card guard** — `CardReview.card` is `SET_NULL`. Filter `card__isnull=False` in `study_review` to prevent `None` PKs entering `session_cards`.

---

## Phase 1: study_review view + URL + template updates

### Overview

Add `from datetime import timedelta` import, add the `study_review` POST-only view, register its URL, and make two changes to `session_results.html`.

### Changes Required

#### 1. Add `timedelta` import

**File**: `flashcards/views.py`

**Intent**: `study_review` needs `timedelta` for the 2-hour window calculation — not yet in the file's import block.

**Contract**: Add `from datetime import timedelta` to the import block at the top of the file.

#### 2. `study_review` view

**File**: `flashcards/views.py`

**Intent**: POST-only view that identifies the user's last-session wrong cards via a 2-hour time window, initialises the session dict with those card IDs, and redirects to the study view. Redirects to topics with a flash message if the user has no history or no wrong cards.

**Contract**:

-   `@login_required`; returns `HttpResponseNotAllowed(['POST'])` on GET.
-   `latest = CardReview.objects.filter(user=request.user).latest('reviewed_at')` — if `CardReview.DoesNotExist`, `messages.warning(request, ...)` + redirect to `flashcards:topics`.
-   `window_start = latest.reviewed_at - timedelta(hours=2)`.
-   `wrong_ids = list(CardReview.objects.filter(user=request.user, reviewed_at__gte=window_start, is_correct=False, card__isnull=False).values_list('card_id', flat=True).distinct())`.
-   If `wrong_ids` is empty: `messages.info(request, ...)` + redirect to `flashcards:topics`.
-   Otherwise: `random.shuffle(wrong_ids)`; set all five `_SESSION_KEYS` with `session_topic_id = None`; redirect to `flashcards:study`.

#### 3. Register `study_review` URL

**File**: `flashcards/urls.py`

**Intent**: Register the new route in the study URL group.

**Contract**: `path('study/review/', views.study_review, name='study_review')` — placed immediately after the `study/results/` entry and before the `study/` entry.

#### 4. Guard "Study again" button

**File**: `flashcards/templates/flashcards/session_results.html`

**Intent**: Prevent the "Study again" form from rendering during a review session when `topic_id` is `None`.

**Contract**: Wrap the existing "Ucz się ponownie" `<form>` in `{% if topic_id %}...{% endif %}`.

#### 5. Add "Review missed cards" button

**File**: `flashcards/templates/flashcards/session_results.html`

**Intent**: Offer a review entry point below the missed-cards list, visible only when there are missed cards.

**Contract**: Inside the existing `{% if missed_cards %}` block, after the `<ul>` list, add a `<form method="post" action="{% url 'flashcards:study_review' %}">` with `{% csrf_token %}` and a submit button with label "Powtórz błędne karty" (Bootstrap `btn btn-warning`). This form sits inside the missed-cards card component, not in the top actions row.

### Success Criteria

#### Automated Verification

-   `uv run python manage.py test flashcards` passes with no regressions

#### Manual Verification

-   After a session with missed cards, "Powtórz błędne karty" button appears on results screen
-   Clicking it starts a new session; progress shows "Karta 1 z N" where N equals the missed-card count
-   After a perfect session, "Powtórz błędne karty" button is absent
-   "Ucz się ponownie" button is absent on results screen after a review session
-   "Wybierz temat" button works from both regular and review results screens

**Implementation Note**: After automated verification passes, confirm all manual steps before starting Phase 2.

---

## Phase 2: Integration Tests

### Overview

Write the integration test suite covering the full review lifecycle and all guard conditions.

### Changes Required

#### 1. Review session tests

**File**: `flashcards/tests.py`

**Intent**: Cover all guard conditions, the happy path, and template conditionals in a new `SpacedRepetitionTests` class.

**Contract**: Five test cases, each using `self.client.force_login(user)`:

-   `test_review_start_no_history_redirects`: User has no CardReview records → POST `study_review` → assert 302 to topics + warning message in `_messages`.
-   `test_review_start_no_wrong_cards_redirects`: All CardReview records within last 2 hours are `is_correct=True` → POST `study_review` → assert 302 to topics + info message.
-   `test_review_session_happy_path`: Create 3 CardReview records within last 2 hours (2 with `is_correct=False`, 1 with `is_correct=True`); POST `study_review`; assert redirect to `flashcards:study`; assert `len(self.client.session['session_cards']) == 2`; GET study twice + POST both; assert final redirect to `study_results`.
-   `test_review_results_hides_study_again_button`: After `study_review` initialises session with `session_topic_id=None`, GET `study_results`; assert the `study_start` URL does not appear in `response.content`.
-   `test_review_button_visible_when_missed_cards_exist`: Complete a regular session (via `session_start`) with at least 1 wrong answer; GET `study_results`; assert the `study_review` URL appears in `response.content`.

### Success Criteria

#### Automated Verification

-   `uv run python manage.py test flashcards` passes all 5 new test cases with no regressions

#### Manual Verification

-   Full E2E: complete session with missed cards → click "Powtórz błędne karty" → answer all review cards → results screen shows correct score → "Ucz się ponownie" absent, "Wybierz temat" present

**Implementation Note**: Once all 5 tests pass and E2E confirmed, this plan is complete.

---

## Testing Strategy

### Unit Tests

Not required — `study_review` logic is fully covered by integration tests.

### Integration Tests

-   Guard: no history → redirect with warning
-   Guard: no wrong cards → redirect with info message
-   Happy path: correct card subset from time window; session initialised with wrong IDs only
-   Results template: "Study again" hidden when `topic_id` is None
-   Results template: "Review" button visible after session with missed cards

### Manual Testing Steps

1.  Complete a session with mixed correct/incorrect answers
2.  On results screen: confirm missed cards list and "Powtórz błędne karty" button
3.  Click review button → confirm card count = missed count
4.  Answer all review cards → confirm results screen, correct score
5.  Confirm "Ucz się ponownie" absent, "Wybierz temat" present
6.  Complete a perfect session → confirm review button absent

## Performance Considerations

Two small queries per review-session start: one `latest()` (O(log N) via index) + one range filter (O(K) where K = reviews in the last 2 hours). Both use the existing `(user, reviewed_at)` index. Negligible at MVP scale.

## Migration Notes

No new models or fields. No migrations required.

## References

-   PRD: `context/foundation/prd.md` (FR-006)
-   Roadmap: `context/foundation/roadmap.md` (S-04, change ID `spaced-repetition-review`)
-   Session dict contract: `context/changes/complete-study-session/plan.md` (Critical Implementation Details)
-   Prerequisite: S-01 (`complete-study-session`) — `_SESSION_KEYS`, `study_card`, `session_results`

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append `— <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: study_review view + URL + template updates

#### Automated

- [x] 1.1 `uv run python manage.py test flashcards` passes with no regressions — 77b9975

#### Manual

- [x] 1.2 After a session with missed cards, "Powtórz błędne karty" button appears on results screen
- [x] 1.3 Clicking it starts a new session with N = missed-card count
- [x] 1.4 After a perfect session, the review button is absent
- [x] 1.5 "Ucz się ponownie" button absent after a review session
- [x] 1.6 "Wybierz temat" works from both regular and review results screens

### Phase 2: Integration Tests

#### Automated

- [x] 2.1 `uv run python manage.py test flashcards` passes all 5 new test cases with no regressions — 8f17d5a

#### Manual

- [x] 2.2 Full E2E: session with missed cards → review → results → score correct, buttons correct