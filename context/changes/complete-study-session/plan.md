# Kompletna Sesja Nauki — Implementation Plan

## Overview

Replace the current stateless random-card loop with a three-screen session flow: topic selection → ordered deck traversal → score screen. A user selects a topic, flips through all its cards one at a time (shuffled, progress-tracked), marks each correct or incorrect, and lands on a results screen showing their score, percentage, and a list of cards they missed.

Assumes F-02 (Topic model, Card→Topic FK, seeded data) is already implemented before this plan executes.

## Current State Analysis

- `flashcards/views.py:28` — `study` view picks one random `Card` on every GET from the full card pool, with no session boundary, no ordering, and no end state. After a POST it redirects back to itself for another random card.
- `flashcards/models.py` — `Card` and `CardReview` exist; no `Topic` model, no `StudySession` model. `CardReview` stores `user`, `card`, `reviewed_at`, `is_correct`.
- `flashcards/templates/flashcards/study.html` — single-card reveal UI; uses JavaScript to show answer, then two POST forms (correct/incorrect).
- `config/urls.py:40` — `HomeView.dispatch` redirects authenticated users directly to `flashcards:study`; `RegisterView.form_valid` does the same.
- `base.html:57` — "Nauka" nav link points to `flashcards:study`.
- `stats/templates/stats/dashboard.html:82` — "Zacznij naukę" CTA links to `flashcards:study`.
- No topic selection screen exists anywhere in the app.

## Desired End State

After this plan is complete:

1. Authenticated users landing on `/` are redirected to `/flashcards/topics/`, which lists all available topics.
2. Selecting a topic POSTs to `/flashcards/study/start/`, initializing a shuffled session in the Django session dict, then redirects to `/flashcards/study/`.
3. `/flashcards/study/` shows one card at a time with a "Card N of M" progress indicator. Answering a card records a `CardReview` and advances the index.
4. After the last card, the user is redirected to `/flashcards/study/results/`, which shows score (X/N, %), a list of missed card questions, a "Study again" button (restart same topic), and a "Choose topic" button.
5. Visiting `/flashcards/topics/` at any point clears in-progress session state.

### Key Discoveries

- `CardReview` records are created on each answer — the existing `stats/services.py:compute_study_stats` will automatically pick them up with no changes needed.
- Django's built-in session middleware is sufficient for state storage; no new DB models are required for MVP.
- Three existing redirects hardcode `flashcards:study` and must be updated: `config/urls.py` (HomeView + RegisterView), `templates/base.html` (navbar), `stats/templates/stats/dashboard.html` (CTA button).
- F-02's `Topic` model will live in the `flashcards` app; this plan imports it from there.

## What We're NOT Doing

- No `StudySession` DB model — session state lives in the Django session dict only.
- No resume of an interrupted session — visiting topics always resets state.
- No per-card time tracking.
- No card ordering other than shuffle (no alphabetical, no difficulty order).
- No spaced-repetition logic (that is S-04).
- No leaderboard update (that is S-02).
- No changes to the existing card-list view at `/flashcards/` or the card-create view.

## Implementation Approach

Three phases that each leave the app in a testable state:

1. **Topic entry point** — add the topic selection screen and update all inbound links/redirects. After phase 1, navigation is correct even though the study session itself is not yet session-aware.
2. **Session loop** — wire up `study_start` and rewrite `study_card` to be session-aware. After phase 2, a user can flip through a full deck and land on the (not yet implemented) results URL.
3. **Score screen + tests** — implement the results view and template, then add the full integration test suite.

## Critical Implementation Details

**Session dict key contract** — the following keys are shared across three views and must be spelled exactly as defined here. A typo causes silent `KeyError` failures:

```
request.session['session_topic_id']  = int   # Topic PK
request.session['session_cards']     = list  # shuffled Card PKs, e.g. [3, 7, 2, 9, ...]
request.session['session_index']     = int   # 0-based position of current card
request.session['session_score']     = int   # running count of correct answers
request.session['session_wrong_ids'] = list  # Card PKs where is_correct=False
```

These five keys are set atomically in `session_start`, read in `study_card` and `session_results`, and deleted in `session_results` (and on GET of topics).

---

## Phase 1: Topic Selection Entry Point

### Overview

Create the topic selection page at `/flashcards/topics/`, and update all three existing hardcoded redirects/links that point to `flashcards:study` so that navigation is consistent after this phase.

### Changes Required

#### 1. Home + register redirects

**File**: `config/urls.py`

**Intent**: Both `HomeView.dispatch` (line 40) and `RegisterView.form_valid` (line 34) redirect authenticated users to `flashcards:study`. Change both to `flashcards:topics` so logged-in and newly registered users land on topic selection.

**Contract**: Two occurrences of `redirect('flashcards:study')` → `redirect('flashcards:topics')`.

#### 2. Navbar link

**File**: `templates/base.html`

**Intent**: The "Nauka" nav item (line 57) currently links to `flashcards:study`. Update it to `flashcards:topics`.

**Contract**: `href="{% url 'flashcards:topics' %}"` and update the active-path check from `/flashcards/study/` to `/flashcards/topics/`.

#### 3. Stats dashboard CTA

**File**: `stats/templates/stats/dashboard.html`

**Intent**: The "Zacznij naukę" button (line 82) links to `flashcards:study`. Update it to `flashcards:topics`.

**Contract**: `href="{% url 'flashcards:topics' %}"`.

#### 4. TopicsListView

**File**: `flashcards/views.py`

**Intent**: Add a `TopicsListView` that clears any stale session state on GET (implementing the "always restart" rule) and passes all `Topic` objects to the template.

**Contract**: `LoginRequiredMixin` + `ListView`; override `get()` to delete the five session keys before calling `super().get()`; `model = Topic`; `template_name = 'flashcards/topics.html'`; `context_object_name = 'topics'`.

#### 5. Topics URL

**File**: `flashcards/urls.py`

**Intent**: Register the new route.

**Contract**: `path('topics/', views.TopicsListView.as_view(), name='topics')` — add at the top of `urlpatterns`.

#### 6. Topics template

**File**: `flashcards/templates/flashcards/topics.html`

**Intent**: Display all topics as selectable cards. Each topic has a POST form targeting `study_start` with the topic's PK. Empty state shows a message when no topics exist.

**Contract**: Extends `base.html`; each topic card renders:
```html
<form method="post" action="{% url 'flashcards:study_start' %}">
  {% csrf_token %}
  <input type="hidden" name="topic_id" value="{{ topic.pk }}">
  <button type="submit" class="btn btn-primary">Zacznij naukę</button>
</form>
```
Empty list state: `<p>Brak tematów. Dodaj tematy przez <a href="/admin/">panel admina</a>.</p>`

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards` passes with no regressions

#### Manual Verification

- Visiting `/` while logged in redirects to `/flashcards/topics/`
- Registering a new account redirects to `/flashcards/topics/`
- Clicking "Nauka" in the navbar goes to `/flashcards/topics/`
- The topics page renders (uses Topic model from F-02); seeded topics are listed
- "Zacznij naukę" on the stats dashboard goes to `/flashcards/topics/`

**Implementation Note**: After phase 1 automated verification passes, confirm the manual steps above before starting phase 2.

---

## Phase 2: Session Initialization + Card Loop

### Overview

Wire up `session_start` (initializes the session dict) and rewrite the `study` view to be session-aware. After this phase a user can flip through a complete deck and be redirected to the results URL (which does not yet exist — a 404 there is expected until phase 3).

### Changes Required

#### 1. `session_start` view

**File**: `flashcards/views.py`

**Intent**: POST-only view that validates the topic, shuffles its card IDs into the session dict, and redirects to the study URL. If the topic has no cards, it redirects to topics with a warning message instead of starting a session.

**Contract**: `@login_required`; returns `HttpResponseNotAllowed(['POST'])` on GET; reads `topic_id` from `request.POST`; calls `get_object_or_404(Topic, pk=topic_id)`; if `topic.cards.count() == 0`: `messages.warning(request, "Ten temat nie ma jeszcze fiszek.")` + redirect to `flashcards:topics`; otherwise initializes the five session keys (see Critical Implementation Details) and redirects to `flashcards:study`.

#### 2. Rewrite `study` view

**File**: `flashcards/views.py`

**Intent**: Replace the existing random-card `study` function with a `study_card` function that reads session state. GET renders the current card with progress. POST records the answer, updates session state, and redirects — either to the next card or to results after the last card.

**Contract**:
- Function name changes from `study` to `study_card` (URL name `study` is preserved in urls.py — no template or link changes needed).
- GET: if `session_cards` not in `request.session` → redirect to `flashcards:topics`; else fetch `Card.objects.get(pk=session_cards[session_index])`; render `flashcards/study.html` with `card`, `current=session_index+1`, `total=len(session_cards)`.
- POST: read `card_id` and `is_correct` from `request.POST`; create `CardReview(user=request.user, card=card, is_correct=is_correct)`; if correct increment `session_score`; else append `card_id` to `session_wrong_ids`; increment `session_index`; if `session_index >= len(session_cards)` redirect to `flashcards:study_results`; else redirect to `flashcards:study`.

#### 3. Study + start URLs

**File**: `flashcards/urls.py`

**Intent**: Register `study_start`; update the `study` path to point to the new `study_card` function.

**Contract**: Add `path('study/start/', views.session_start, name='study_start')` before the existing `study/` entry; change `views.study` → `views.study_card` on the `study` path.

#### 4. Update study template

**File**: `flashcards/templates/flashcards/study.html`

**Intent**: Add a session progress indicator above the question so the user knows how far through the deck they are.

**Contract**: Add `<p class="text-muted small">Karta {{ current }} z {{ total }}</p>` (or a Bootstrap progress bar with `value="{{ current }}" max="{{ total }}"`) immediately above the question `<h3>`. Existing reveal button and correct/incorrect forms are unchanged.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards` passes
- GET `/flashcards/study/` with no session cookie returns 302 to `/flashcards/topics/`
- POST to `/flashcards/study/start/` with a valid topic_id containing cards returns 302 to `/flashcards/study/`

#### Manual Verification

- Selecting a topic and clicking "Zacznij naukę" starts a session; card 1 of N is shown with the correct total
- Answering cards advances the progress indicator correctly
- After answering the last card, the browser navigates to `/flashcards/study/results/` (404 expected until phase 3)
- Topic with zero cards redirects to topics page with a warning message

**Implementation Note**: The 404 on `/flashcards/study/results/` after the last card is expected at end of phase 2. Confirm all other manual steps before starting phase 3.

---

## Phase 3: Score Screen + Integration Tests

### Overview

Implement the results view and template, then write the full integration test suite covering the happy path and all guard conditions.

### Changes Required

#### 1. `session_results` view

**File**: `flashcards/views.py`

**Intent**: GET-only view that reads the completed session's score data from the session dict, fetches missed card objects, clears all session keys, and renders the results template. Guards against direct URL access (no active session) by redirecting to topics.

**Contract**: `@login_required`; if `session_cards` absent from `request.session` → redirect to `flashcards:topics`; read `score = session['session_score']`, `total = len(session['session_cards'])`, `wrong_ids = session['session_wrong_ids']`, `topic_id = session['session_topic_id']`; `missed_cards = Card.objects.filter(pk__in=wrong_ids)`; `percent = round(score / total * 100) if total else 0`; delete all five session keys; render `flashcards/session_results.html` with `score`, `total`, `percent`, `missed_cards`, `topic_id`.

#### 2. Results URL

**File**: `flashcards/urls.py`

**Intent**: Register `/flashcards/study/results/` before the `/flashcards/study/` entry so Django's URL resolver doesn't shadow it.

**Contract**: `path('study/results/', views.session_results, name='study_results')` — placed immediately before the `study/` entry.

#### 3. Results template

**File**: `flashcards/templates/flashcards/session_results.html`

**Intent**: Display the session score, percentage, and missed card questions. Provide "Study again" (restart same topic) and "Choose topic" (topics page) as the two exit actions.

**Contract**: Extends `base.html`; title block: "Wynik sesji"; renders score summary as `{{ score }} / {{ total }} ({{ percent }}%)`; lists missed cards as `<ul>{% for card in missed_cards %}<li>{{ card.question }}</li>{% endfor %}</ul>` (empty state: "Idealny wynik! Żadnych błędów."); "Study again" is a POST form to `flashcards:study_start` with `<input type="hidden" name="topic_id" value="{{ topic_id }}">` and `{% csrf_token %}`; "Choose topic" is `<a href="{% url 'flashcards:topics' %}">`.

#### 4. Integration tests

**File**: `flashcards/tests.py`

**Intent**: Cover the full session lifecycle and all guard conditions with the Django test client. Tests create their own `Topic` and `Card` fixtures (relies on F-02 model being present).

**Contract**: Five test cases, each using `self.client.force_login(user)`:

- `test_full_session_happy_path`: POST to `study_start` with a topic containing 3 cards → loop: GET `study` + POST with alternating `is_correct=1`/`0` × 3 → final POST redirects to `study_results` → GET `study_results` → assert `score=2`, `total=3`, `percent=67`, missed cards list has 1 item, session keys absent after render.
- `test_empty_deck_redirects`: POST `study_start` with topic that has 0 cards → assert 302 to `topics` + warning message in response.
- `test_study_without_session_redirects`: GET `/flashcards/study/` with no prior session → assert 302 to `/flashcards/topics/`.
- `test_results_without_session_redirects`: GET `/flashcards/study/results/` with no prior session → assert 302 to `/flashcards/topics/`.
- `test_visiting_topics_clears_session`: set five session keys manually via `self.client.session` → GET `/flashcards/topics/` → assert all five keys absent from session.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards` passes all 5 new test cases with no regressions

#### Manual Verification

- Complete end-to-end flow: log in → `/flashcards/topics/` → select topic → answer all cards → results screen shows correct score, percentage, and missed card question list
- Score is accurate: manually count correct POSTs and verify X/N matches
- "Study again" button starts a new shuffled session on the same topic (card order different from previous run)
- Clicking "Nauka" navbar mid-session (going to `/flashcards/topics/`) then starting a new session starts from card 1 of the new topic
- Stats dashboard (`/stats/`) reflects the newly created `CardReview` records after a completed session

**Implementation Note**: Once all 5 tests pass and manual E2E is confirmed, this plan is complete. Run `/10x-archive complete-study-session` to close the change.

---

## Testing Strategy

### Unit Tests

Not required separately — session logic is covered by integration tests via the Django test client.

### Integration Tests

- Happy path: full session with mixed correct/incorrect answers; assert score accuracy and session cleanup
- Empty deck guard: topic with 0 cards → redirect to topics
- Session guards: direct access to `/study/` and `/results/` without session → redirect to topics
- Session reset: visiting topics clears session state

### Manual Testing Steps

1. Log in; confirm redirect to `/flashcards/topics/`
2. Select a topic (requires F-02 seeded data); confirm card 1 of N shown with progress indicator
3. Answer all cards with mix of correct/incorrect; confirm progress indicator increments each time
4. After last card, confirm redirect to `/flashcards/study/results/`
5. Confirm score (X/N, %) matches answers given; missed cards list shows correct questions
6. Click "Study again" — confirm new session starts, card order differs (shuffled)
7. Mid-session: click "Nauka" navbar link → topics page → select topic → new session starts from card 1
8. Visit `/stats/` — confirm today's review count includes cards just answered

## Performance Considerations

All queries are O(N) where N is deck size (expected 10–100 cards at MVP). No caching needed.

## Migration Notes

No new models introduced in this plan. No data migrations required. Existing `CardReview` records are compatible; the stats dashboard continues to work unchanged.

## References

- PRD: `context/foundation/prd.md` (FR-001, FR-002, FR-003, FR-004, US-01)
- Roadmap: `context/foundation/roadmap.md` (S-01, change ID `complete-study-session`)
- Prerequisite: F-02 change (`topic-deck-model`) must be implemented first

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Topic Selection Entry Point

#### Automated

- [x] 1.1 `uv run python manage.py test flashcards` passes with no regressions — 62248fa

#### Manual

- [x] 1.2 Visiting `/` while logged in redirects to `/flashcards/topics/` — 62248fa
- [x] 1.3 Registering a new account redirects to `/flashcards/topics/` — 62248fa
- [x] 1.4 Clicking "Nauka" in the navbar goes to `/flashcards/topics/` — 62248fa
- [x] 1.5 Topics page renders; seeded topics are listed — 62248fa
- [x] 1.6 "Zacznij naukę" on stats dashboard goes to `/flashcards/topics/` — 62248fa

### Phase 2: Session Initialization + Card Loop

#### Automated

- [x] 2.1 `uv run python manage.py test flashcards` passes — fbaec0d
- [x] 2.2 GET `/flashcards/study/` with no session returns 302 to `/flashcards/topics/` — fbaec0d
- [x] 2.3 POST to `/flashcards/study/start/` with valid topic returns 302 to `/flashcards/study/` — fbaec0d

#### Manual

- [x] 2.4 Selecting a topic starts a session; card 1 of N shown with correct total — fbaec0d
- [x] 2.5 Answering cards advances the progress indicator correctly — fbaec0d
- [x] 2.6 After last card, browser navigates to `/flashcards/study/results/` — fbaec0d
- [x] 2.7 Topic with zero cards redirects to topics with warning message — fbaec0d

### Phase 3: Score Screen + Integration Tests

#### Automated

- [x] 3.1 `uv run python manage.py test flashcards` passes all 5 new test cases with no regressions

#### Manual

- [x] 3.2 Complete E2E flow works: log in → topics → start → answer all → results with correct score
- [x] 3.3 Score (X/N, %) is accurate for the answers given
- [x] 3.4 "Study again" starts a new shuffled session on the same topic
- [x] 3.5 Mid-session navbar click → topics → new session starts from card 1
- [x] 3.6 Stats dashboard reflects newly created CardReview records after a completed session
