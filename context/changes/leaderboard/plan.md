# Leaderboard — Implementation Plan

## Overview

Add a `/stats/leaderboard/` page that shows the top 10 users ranked by cumulative correct answers across all study sessions, descending, with ties broken alphabetically. A "Ranking" nav link in the navbar makes it accessible from any authenticated page.

## Current State Analysis

- `CardReview` model (`flashcards/models.py`) has `user` (FK, `related_name='card_reviews'`) + `is_correct` (boolean). A single annotated query yields all user totals.
- `stats/services.py` uses the service-function pattern: pure function injected into view context via `get_context_data`. Leaderboard follows this same pattern.
- `stats/views.py` has one view (`StatsDashboardView`). Leaderboard adds a second.
- `stats/urls.py` has one route. Leaderboard adds a second.
- The navbar (`templates/base.html:54–78`) has four authenticated links: Nauka, Fiszki, Dodaj, Statystyki. "Ranking" is added after Statystyki.
- No migrations needed — no new models or fields.

## Desired End State

A logged-in user can navigate to `/stats/leaderboard/` (or click "Ranking" in the navbar) and see a table listing the top 10 users by total correct answers, with their rank and their row highlighted if it's the current user.

### Key Discoveries

- `CardReview.user` has `related_name='card_reviews'` — annotated query uses `Count('card_reviews', filter=Q(card_reviews__is_correct=True))`.
- `CardReview.Meta.indexes = [Index(fields=['user', 'reviewed_at'])]` — the leaderboard query does not filter by `reviewed_at`, so this index is not used here; full scan of CardReview is acceptable at MVP scale.
- `StudyStats` is a frozen dataclass in `stats/types.py`; leaderboard data is a plain QuerySet — no new type needed.

## What We're NOT Doing

- No pagination — top 10 only.
- No "current user's row pinned below top 10" when outside the top 10.
- No stats dashboard integration — standalone page + navbar only.
- No public (unauthenticated) access.
- No per-topic breakdown.

## Implementation Approach

Two phases: Phase 1 wires the backend end-to-end (service + view + URL) leaving a skeleton template. Phase 2 completes the template, adds the navbar link, and adds tests. After Phase 1 a developer can verify the view returns 200 before touching the template.

---

## Phase 1: Backend — Service, View, URL

### Overview

Add `get_leaderboard()` to `stats/services.py`, add `LeaderboardView` to `stats/views.py`, and register the route in `stats/urls.py`.

### Changes Required

#### 1. Leaderboard service function

**File**: `stats/services.py`

**Intent**: Add a `get_leaderboard()` function that returns the top 10 users annotated with their total correct count, ordered by descending total then ascending username.

**Contract**: Imports `get_user_model`, `Count`, `Q` from Django. Returns `User.objects.annotate(total_correct=Count('card_reviews', filter=Q(card_reviews__is_correct=True))).order_by('-total_correct', 'username')[:10]`.

#### 2. LeaderboardView

**File**: `stats/views.py`

**Intent**: Add a view that passes the leaderboard queryset to the template.

**Contract**: `LoginRequiredMixin` + `TemplateView`; `template_name = 'stats/leaderboard.html'`; override `get_context_data` to inject `ctx['leaderboard'] = get_leaderboard()`.

#### 3. Leaderboard URL

**File**: `stats/urls.py`

**Intent**: Register the new route and import the new view.

**Contract**: `path('leaderboard/', LeaderboardView.as_view(), name='leaderboard')` — add after the existing dashboard entry.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test` passes with no regressions

#### Manual Verification

- GET `/stats/leaderboard/` returns HTTP 200 for a logged-in user
- GET `/stats/leaderboard/` redirects an unauthenticated user to login

**Implementation Note**: After automated verification passes, confirm the two manual steps before starting Phase 2.

---

## Phase 2: Template + Navbar + Tests

### Overview

Create the leaderboard HTML template, add the "Ranking" navbar link, and write the integration test suite.

### Changes Required

#### 1. Leaderboard template

**File**: `stats/templates/stats/leaderboard.html`

**Intent**: Display the top-10 leaderboard as a Bootstrap table. Highlight the current user's row.

**Contract**: Extends `base.html`; title block: "Ranking — NaukaAI"; Bootstrap table with columns `#`, `Użytkownik`, `Poprawne odpowiedzi`; iterates `{% for entry in leaderboard %}` using `{{ forloop.counter }}` for rank; adds `class="table-primary"` to the row when `entry == request.user`. Empty leaderboard (no reviews yet) renders the table with all users showing 0 — no special empty-state needed.

#### 2. Navbar "Ranking" link

**File**: `templates/base.html`

**Intent**: Add a "Ranking" nav link after the "Statystyki" link so the leaderboard is reachable from any authenticated page.

**Contract**: New `<li class="nav-item">` with `href="{% url 'stats:leaderboard' %}"`, active-path check `{% if request.path == '/stats/leaderboard/' %}bg-primary bg-opacity-25{% endif %}`, icon `bi bi-trophy`, label "Ranking". Inserted immediately after the Statystyki `<li>` block (currently lines 72–76 of `base.html`).

#### 3. Integration tests

**File**: `stats/tests.py` (create if absent)

**Intent**: Cover ranking order, tie-breaking, access control, and the top-10 limit.

**Contract**: Four test cases, each using `self.client.force_login(user)`:

- `test_leaderboard_order`: Create 3 users with 5, 3, and 1 correct CardReview records respectively; GET leaderboard; assert `leaderboard[0].total_correct == 5` and correct descending order.
- `test_leaderboard_tie_broken_alphabetically`: Create users "bravo" and "alpha" each with 2 correct reviews; assert "alpha" appears before "bravo" in response.
- `test_leaderboard_unauthenticated_redirects`: GET `/stats/leaderboard/` without login; assert 302 to login URL.
- `test_leaderboard_top_10_limit`: Create 11 users each with 1 correct review; assert `len(context['leaderboard']) == 10`.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test` passes all 4 new test cases with no regressions

#### Manual Verification

- Navbar shows "Ranking" link; clicking it lands on `/stats/leaderboard/`
- Table shows rank, username, and total correct for each row
- Current user's row is highlighted
- Navbar active state is highlighted when on `/stats/leaderboard/`

**Implementation Note**: Once all 4 tests pass and manual steps confirmed, this plan is complete.

---

## Testing Strategy

### Unit Tests

Not required — `get_leaderboard()` is fully covered by integration tests.

### Integration Tests

- Correct ordering by total_correct descending
- Tie-breaking alphabetically by username
- Access control — unauthenticated redirect
- Top-10 limit enforced

### Manual Testing Steps

1. Log in; click "Ranking" in navbar; confirm `/stats/leaderboard/` loads
2. Confirm your own row is highlighted
3. Log out; visit `/stats/leaderboard/` directly; confirm redirect to login

## Performance Considerations

Single aggregate query over CardReview; O(N) where N is total review records. Acceptable at MVP scale. The `(user, reviewed_at)` index on CardReview is not used by this query.

## Migration Notes

No new models or fields. No migrations required.

## References

- PRD: `context/foundation/prd.md` (FR-005, Business Logic section)
- Roadmap: `context/foundation/roadmap.md` (S-02, change ID `leaderboard`)
- Prerequisite: S-01 (`complete-study-session`) provides the `CardReview` records this query reads

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Backend — Service, View, URL

#### Automated

- [x] 1.1 `uv run python manage.py test` passes with no regressions

#### Manual

- [x] 1.2 GET `/stats/leaderboard/` returns HTTP 200 for a logged-in user
- [x] 1.3 GET `/stats/leaderboard/` redirects unauthenticated user to login

### Phase 2: Template + Navbar + Tests

#### Automated

- [x] 2.1 `uv run python manage.py test` passes all 4 new test cases with no regressions

#### Manual

- [x] 2.2 Navbar shows "Ranking" link; clicking it lands on `/stats/leaderboard/`
- [x] 2.3 Table shows rank, username, and total correct for each row
- [x] 2.4 Current user's row is highlighted
- [x] 2.5 Navbar active state is highlighted when on `/stats/leaderboard/`
