# Leaderboard — Plan Brief

> Full plan: `context/changes/leaderboard/plan.md`

## What & Why

Add a `/stats/leaderboard/` page showing the top 10 users ranked by cumulative correct answers. FR-005 is a PRD must-have and part of the product's motivational loop — users need to see how their study effort compares to others.

## Starting Point

`CardReview` records (user + is_correct) exist and are populated by the completed S-01 study session. No leaderboard view, URL, or template exists. No new models or migrations are needed.

## Desired End State

A logged-in user clicks "Ranking" in the navbar, lands on `/stats/leaderboard/`, and sees a table of the top 10 users ordered by total correct answers (descending), with their own row highlighted. Ties are broken alphabetically by username.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|---|---|---|
| Access control | Logged-in users only | Consistent with all other views; no extra code path |
| Data shown per row | Rank + username + total correct | Minimal, exactly matches PRD spec |
| Display limit | Top 10 | Sufficient for MVP; no pagination complexity |
| Current user outside top 10 | Not shown separately | User chose simplest option |
| Tie-breaking | Alphabetical by username | Deterministic, zero extra queries |
| Dashboard integration | None | Standalone page + navbar link only |
| App location | `stats` app at `/stats/leaderboard/` | Reuses existing app; no new app needed |

## Scope

**In scope:** `get_leaderboard()` service function, `LeaderboardView`, URL registration, leaderboard template, "Ranking" navbar link, 4 integration tests.

**Out of scope:** Pagination, public access, per-topic breakdown, dashboard widget, current-user row pinned outside top 10.

## Architecture / Approach

Follows the existing `stats` app pattern exactly: service function (`get_leaderboard`) → `TemplateView` (`LeaderboardView`) → template. Single annotated QuerySet: `User.objects.annotate(total_correct=Count('card_reviews', filter=Q(is_correct=True))).order_by('-total_correct', 'username')[:10]`.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Backend | Service + view + URL wired; `/stats/leaderboard/` returns 200 | None — straightforward annotation query |
| 2. Template + navbar + tests | Rendered table, navbar link, 4 tests passing | None significant |

**Prerequisites:** S-01 done (CardReview data exists) ✓  
**Estimated effort:** ~1 session across 2 phases

## Open Risks & Assumptions

- The aggregate query does a full scan of `CardReview` — acceptable at MVP scale; will need a covering index if the table grows to millions of rows.

## Success Criteria (Summary)

- GET `/stats/leaderboard/` shows a table with top 10 users by total correct, current user highlighted
- Unauthenticated access redirects to login
- All 4 integration tests pass
