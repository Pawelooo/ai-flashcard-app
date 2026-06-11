---
date: 2026-06-11T00:00:00+02:00
researcher: Pawelooo
git_commit: f8cebadcc50a73ccecda997a74c7e5405753f495
branch: master
repository: ai-flashcard-app
topic: "CRUD Gap Analysis — which operations are missing?"
tags: [research, codebase, crud, flashcards, card, topic, cardreview, views]
status: complete
last_updated: 2026-06-11
last_updated_by: Pawelooo
---

# Research: CRUD Gap Analysis

**Date**: 2026-06-11  
**Researcher**: Pawelooo  
**Git Commit**: f8cebadcc50a73ccecda997a74c7e5405753f495  
**Branch**: master  
**Repository**: ai-flashcard-app

## Research Question

Does the app implement all CRUD operations for its models? Which operations are missing?

## Summary

The app has **4 models** (Topic, Card, CardReview, User) and **2 read-only stat views**. Of the
meaningful CRUD operations, **5 are fully missing** from the user-facing UI, **1 is partially broken**
(card create can't assign a topic), and **3 are admin-panel-only** by intentional design.

The most impactful gap: a user can *create* a card (`/flashcards/create/`) but can
never *edit* or *delete* it, and the create form doesn't even let them pick a topic —
meaning every user-created card is orphaned and will never appear in a study session.

---

## Detailed Findings

### Model Inventory

| Model | App | Fields |
|-------|-----|--------|
| `Topic` | flashcards | name, slug |
| `Card` | flashcards | topic (FK→Topic), question, answer, created_at |
| `CardReview` | flashcards | user (FK), card (FK), reviewed_at, is_correct |
| `User` | django.contrib.auth | username, password, … (built-in) |

---

### Topic — CRUD Matrix

| Operation | Status | Where |
|-----------|--------|-------|
| Create | ⚠️ Admin-only | Django admin panel only (`flashcards/admin.py:4`) |
| Read (List) | ✅ | `TopicsListView` → `GET /flashcards/topics/` (`views.py:24`) |
| Read (Detail) | ❌ Missing | No single-topic detail view |
| Update | ⚠️ Admin-only | Django admin panel only |
| Delete | ⚠️ Admin-only | Django admin panel only |

**Admin-only is intentional** — FR-007 (must-have) says admin creates topic decks.
S-03 in the roadmap is blocked on the admin-role decision (PRD Open Question #3:
superuser vs. separate role vs. management command only).

---

### Card — CRUD Matrix

| Operation | Status | Where |
|-----------|--------|-------|
| Create | ⚠️ Broken | `CardCreateView` → `POST /flashcards/create/` (`views.py:91`) |
| Read (List) | ✅ | `CardListView` → `GET /flashcards/` (`views.py:84`) |
| Read (Detail) | ❌ Missing | No single-card detail view |
| Update | ❌ Missing | No `UpdateView`, no URL, no form |
| Delete | ❌ Missing | No `DeleteView`, no URL, no confirmation template |

**Critical defect in Create:** `CardForm` (`forms.py:7`) only exposes `question` and
`answer` — the `topic` FK is excluded. Every card created through the UI has
`topic = NULL`, making it invisible in any study session (sessions are always
topic-scoped via `topic.cards.values_list` in `views.py:42`).

---

### CardReview — CRUD Matrix

| Operation | Status | Where |
|-----------|--------|-------|
| Create | ✅ (implicit) | Auto-created in `study_card` POST (`views.py:137`) |
| Read (List) | ❌ Aggregate only | `StatsDashboardView` shows totals, not raw rows |
| Read (Detail) | ❌ Missing | Not needed for MVP |
| Update | N/A | Reviews are immutable by design |
| Delete | N/A | Not exposed |

Reviews are append-only event records — Update/Delete being absent is correct design.
The missing raw history view is a future nice-to-have (study history log).

---

### User (Django built-in auth) — CRUD Matrix

| Operation | Status | Where |
|-----------|--------|-------|
| Create | ✅ | `RegisterView` → `POST /accounts/register/` (`config/urls.py:27`) |
| Read (Profile) | ❌ Missing | No profile page or account view |
| Update | ❌ Missing | No edit profile, no password change UI |
| Delete | ❌ Missing | No account deletion |

User profile CRUD is not mentioned in the PRD at all — these gaps are expected for MVP.

---

### Stats Views (Read-only, no model of their own)

| View | URL | Status |
|------|-----|--------|
| `StatsDashboardView` | `GET /stats/` | ✅ |
| `LeaderboardView` | `GET /stats/leaderboard/` | ✅ |

---

## Code References

- `flashcards/views.py:24-33` — `TopicsListView` (Topic Read/List)
- `flashcards/views.py:84-88` — `CardListView` (Card Read/List)
- `flashcards/views.py:91-95` — `CardCreateView` (Card Create)
- `flashcards/views.py:42` — `topic.cards.values_list('id', flat=True)` — why orphaned cards never appear in sessions
- `flashcards/views.py:137` — `CardReview.objects.create(...)` (CardReview Create, implicit)
- `flashcards/forms.py:6-16` — `CardForm` — `fields = ['question', 'answer']` — topic excluded
- `flashcards/models.py:6-12` — `Topic` model
- `flashcards/models.py:14-27` — `Card` model with `topic` FK
- `flashcards/models.py:30-50` — `CardReview` model
- `flashcards/urls.py:1-14` — all registered flashcard URLs
- `flashcards/admin.py:1-6` — admin registrations (all three models)
- `config/urls.py:27-34` — `RegisterView` (User Create)
- `stats/views.py:7-19` — `StatsDashboardView` + `LeaderboardView`

---

## Architecture Insights

1. **Study sessions are always topic-scoped.** `session_start` (`views.py:37`) fetches
   card IDs via `topic.cards.values_list`. Cards without a topic FK are permanently
   excluded from any study flow — not a bug that shows up during development, but a
   silent data trap for user-created cards.

2. **No `UpdateView` / `DeleteView` pattern established.** The codebase uses Django
   class-based views for List and Create but skips Update/Delete entirely. Adding them
   follows the same `LoginRequiredMixin` + CBV pattern already in use.

3. **Admin panel is the only backstop.** All three models are registered in
   `flashcards/admin.py` with bare `admin.site.register()` — no custom `ModelAdmin`,
   no search fields, no list_display tweaks. It functions but is not production-grade.

4. **`CardForm` topic gap is a silent bug.** The form works — POST succeeds, card is
   saved — but the resulting record is useless for the app's primary flow. This is the
   highest-priority defect to fix before any card management UX is shown to users.

---

## Historical Context (from prior changes)

- `context/changes/complete-study-session/change.md` — S-01 (`impl_reviewed`) established
  the session flow that makes topic-scoping mandatory. Card CRUD was out of scope for that slice.
- `context/changes/leaderboard/change.md` — S-02 (`done`) confirmed `CardReview` Create
  is working correctly; no CRUD gaps discovered in that context.
- `context/changes/spaced-repetition-review/change.md` — S-04 (`done`) builds on
  `CardReview` records; also did not require Card Update/Delete.
- `context/foundation/roadmap.md` — S-03 (`blocked`) is the planned path for admin
  topic/deck creation; resolving PRD Open Question #3 unblocks it.

---

## Prioritized Gap List

| # | Gap | Impact | Effort | Notes |
|---|-----|--------|--------|-------|
| 1 | `CardForm` missing `topic` field | 🔴 Critical | XS | Add `topic` to `fields`; user-created cards are otherwise unusable |
| 2 | Card Update (`UpdateView`) | 🟠 High | S | Standard CBV; needs `card_form.html` + URL `cards/<pk>/edit/` |
| 3 | Card Delete (`DeleteView`) | 🟠 High | S | Standard CBV; needs confirm template + URL `cards/<pk>/delete/` |
| 4 | Topic CRUD for users | 🟡 Medium | M | Intentionally admin-only per FR-007; unblocks when S-03 resolves |
| 5 | User profile / password change | 🟡 Medium | S | Not in PRD for MVP; Django auth ships `PasswordChangeView` for free |
| 6 | Card Detail view | 🟢 Low | XS | Optional; card list + study serve the user need |
| 7 | CardReview history | 🟢 Low | S | Nice-to-have; stats dashboard covers the aggregate need |

---

## Open Questions

1. **Should `CardForm` add a `topic` dropdown, or should topic be inferred from context
   (e.g., user is on a topic page when clicking "Add card")?** Context-based UX is
   friendlier but requires a topic detail page to exist first (gap #4 / Topic Read Detail).

2. **Who can create/edit/delete cards?** Currently any logged-in user can create a card.
   Should Update and Delete be owner-only, or admin-only? The PRD's flat user model
   implies any user can manage content, but this was never explicitly decided.

3. **Does the Card List view need to filter by topic?** Currently `CardListView` shows
   ALL cards regardless of topic. With many cards this becomes unwieldy — a topic filter
   or per-topic card list would help, but that depends on resolving gap #1 first.