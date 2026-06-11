# Card CRUD Completion — Plan Brief

> Full plan: `context/changes/crud-gap-analysis/plan.md`
> Research: `context/changes/crud-gap-analysis/research.md`

## What & Why

Complete the missing CRUD operations for the `Card` model. The app already has Create and List, but a silent bug in Create orphans every user-made card (`topic = NULL` means they never appear in study sessions), and there's no way to Edit or Delete from the UI.

## Starting Point

`CardCreateView` exists at `/flashcards/create/` but `CardForm` only exposes `question` and `answer` — `topic` is excluded. `Card` has no `created_by` field. No Update, Delete, or Detail views exist. Cards are shown as a static grid with no navigation.

## Desired End State

Creating a card lets the user pick a topic (dropdown) and the card is tagged with `created_by`. Each card in the list is clickable, leading to a detail page. The detail page shows Edit and Delete actions to the owner and staff; other users see read-only. Staff can manage all cards including seeded ones with no owner.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| Auth model | Owner OR staff | Matches PRD flat model; prevents random overwrites without full lock-out | Plan |
| Null owner handling | Staff-only | Safe default for seeded/existing content with no clear owner | Plan |
| Topic assignment UX | Dropdown in CardForm | One-line change, works today, no extra views required | Research |
| List navigation | Via card detail page | Richer UX chosen over direct edit buttons on tiles | Plan |
| Delete confirmation | Separate page (Django DeleteView) | Matches existing CBV pattern; no JavaScript needed | Plan |

## Scope

**In scope:** `created_by` FK + migration, `topic` dropdown in CardForm, Card Detail view, Card Update view, Card Delete view, shared permission mixin (owner/staff)

**Out of scope:** Topic CRUD for users (admin-only per FR-007), CardReview history, User profile/password change, inline JS editing, Card Detail view as its own distinct roadmap slice

## Architecture / Approach

Three sequential phases, each independently testable: (1) data foundation — model change + form fix, (2) detail view — read path that Update/Delete will link back to, (3) write mutations behind a shared `CardEditPermissionMixin`. No new models beyond the `created_by` FK. All views follow the existing `LoginRequiredMixin + CBV` pattern already in the codebase.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Data Foundation | `created_by` FK, migration, topic dropdown, auto-set owner on create | Migration null default on existing rows (handled: `null=True`) |
| 2. Card Detail | Navigable detail page; Edit/Delete shown conditionally via `can_edit` flag | Correct `can_edit` wiring in template |
| 3. Update & Delete | Full edit/delete behind permission mixin; dynamic form title | Permission mixin MRO order in CBV inheritance |

**Prerequisites:** None — starts from current master branch.
**Estimated effort:** ~1-2 sessions across 3 phases

## Open Risks & Assumptions

- Existing seeded cards (via `seed_cards` command) will have `created_by = NULL` and are staff-only by design. If the user wants to own those cards, they'd need to update them manually via the Django admin or shell.
- `CardForm` `topic` field shows ALL topics in a single dropdown. If the topic list grows large, a search-enabled widget would help, but is out of scope.

## Success Criteria (Summary)

- A new card created via the UI is assigned a topic and appears in a study session for that topic
- A logged-in owner can edit and delete their own cards; non-owners attempting direct URL access get 403
- Staff can manage all cards including seeded ones with null owner