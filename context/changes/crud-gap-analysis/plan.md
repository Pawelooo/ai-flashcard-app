# Card CRUD Completion — Implementation Plan

## Overview

Complete the missing CRUD operations for the `Card` model: fix the silent orphaned-card bug in Create, add a Detail view, and add Update/Delete with an owner-or-staff permission guard.

## Current State Analysis

- `CardCreateView` exists at `/flashcards/create/` but `CardForm` omits `topic`, producing cards with `topic = NULL` that are invisible to every study session (`views.py:42`).
- No `created_by` field on `Card` — owner tracking is impossible without a migration.
- No `CardDetailView`, `CardUpdateView`, or `CardDeleteView`.
- `card_list.html` shows cards in a static grid with no navigation to a detail page.
- `card_form.html` renders fields generically via `{% for field in form %}` — can be reused for both Create and Update with a template-level title swap.
- All existing views follow `LoginRequiredMixin + CBV` — new views use the same pattern.

## Desired End State

- Creating a card lets the user pick a topic via dropdown; `created_by` is auto-set to the logged-in user.
- Every card tile in the list links to a detail page showing the full question, answer, and topic.
- The detail page shows Edit and Delete actions only to the card's owner or a staff user.
- Update pre-fills the edit form and redirects to the card detail on success.
- Delete shows a confirmation page before removing the record.
- Cards with no owner (existing seeded/migrated data) are editable by staff only.

### Key Discoveries

- `CardForm` (`forms.py:7`) uses `{% for field in form %}` rendering — adding `topic` to `fields` auto-renders as a `ModelChoiceField` select with no template changes needed.
- `card_form.html` title "Nowa fiszka" is hardcoded — can be made dynamic with `{% if object %}` (Django sets `object = None` for CreateView, the Card instance for UpdateView).
- `topic.cards.values_list()` at `views.py:42` is the exact reason `topic = NULL` silently excludes user-created cards from sessions.
- The permission mixin null-owner case is handled automatically: `None == request.user` is always `False`, so null-owner cards fall through to staff-only without special-case logic.

## What We're NOT Doing

- No Topic CRUD for users (intentionally admin-only per FR-007 / roadmap S-03).
- No Card Detail inline editing (would require JavaScript).
- No CardReview history view.
- No User profile / password change.
- No changes to the existing study session flow.

## Implementation Approach

Three sequential phases, each independently testable:

1. **Foundation** — data model + form fix (prerequisite for everything else)
2. **Detail view** — read path; makes cards navigable; required before Update/Delete can link back
3. **Update + Delete** — write mutations behind a shared permission mixin

The permission mixin is a single helper used by both `CardUpdateView` and `CardDeleteView` to avoid duplicating the owner/staff check.

## Critical Implementation Details

**Permission logic for null owner:** The mixin checks `obj.created_by == request.user`. For existing cards where `created_by` is `NULL`, this evaluates to `None == request.user` which is always `False` — they correctly fall through to staff-only. No special null handling is needed.

**URL ordering:** `<int:pk>/` matches only numeric path segments, so it won't conflict with string-prefix routes (`topics/`, `study/`, `create/`). Add pk-based paths after the existing string-prefix patterns.

---

## Phase 1: Data Foundation

### Overview

Add `created_by` FK to `Card`, generate the migration, fix `CardForm` to expose `topic`, and update `CardCreateView` to auto-set `created_by` on save.

### Changes Required

#### 1. Card model — add `created_by` field

**File**: `flashcards/models.py`

**Intent**: Add a nullable `created_by` FK to the User model on `Card`. Nullable so existing rows keep their data without a default value; `SET_NULL` on delete means cards survive user deletion.

**Contract**: `created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_cards')`

#### 2. Migration

**File**: `flashcards/migrations/` (auto-generated)

**Intent**: Run `uv run python manage.py makemigrations flashcards` to generate the migration for the `created_by` field. Verify with `--check` before applying.

#### 3. CardForm — add `topic` field with Bootstrap widget

**File**: `flashcards/forms.py`

**Intent**: Add `'topic'` to `fields` so the create/edit form includes a topic dropdown. Add a `form-select` Bootstrap widget (note: Bootstrap uses `form-select` for `<select>`, not `form-control`).

**Contract**: `fields = ['topic', 'question', 'answer']`; `widgets` dict gets `'topic': forms.Select(attrs={'class': 'form-select'})`.

#### 4. CardCreateView — auto-set `created_by`

**File**: `flashcards/views.py`

**Intent**: Override `form_valid()` to stamp `created_by` with the current user before the record is saved. Without this, the field stays `NULL` for all new cards even after the migration.

**Contract**: Set `form.instance.created_by = self.request.user` then call `return super().form_valid(form)`.

### Success Criteria

#### Automated Verification

- `uv run python manage.py makemigrations --check` exits 0 (migration was generated, nothing pending)
- `uv run python manage.py migrate` applies cleanly
- `uv run python manage.py test flashcards` passes

#### Manual Verification

- Visit `/flashcards/create/` — topic dropdown is present
- Create a card with a topic — verify the card appears in a study session for that topic
- Verify `Card.created_by` is set to the logged-in user after creation (Django shell or admin panel)

**Implementation Note**: After automated verification passes, pause for manual confirmation before proceeding to Phase 2.

---

## Phase 2: Card Detail View

### Overview

Add `CardDetailView` with its URL and template. Update `card_list.html` so each card tile links to the detail page. The detail template shows Edit/Delete buttons only when the viewer is the owner or staff.

### Changes Required

#### 1. CardDetailView

**File**: `flashcards/views.py`

**Intent**: Standard `DetailView` enriched with a `can_edit` context variable — `True` when `card.created_by == request.user` or `request.user.is_staff`. The template uses this flag to conditionally render Edit/Delete actions.

**Contract**: `LoginRequiredMixin + DetailView`, `model = Card`, `template_name = 'flashcards/card_detail.html'`, `context_object_name = 'card'`. Override `get_context_data` to inject `can_edit`. Add `DetailView` to the existing `from django.views.generic import` line.

#### 2. URL for card detail

**File**: `flashcards/urls.py`

**Intent**: Register the detail view after existing string-prefix routes to avoid any path ambiguity.

**Contract**: `path('<int:pk>/', views.CardDetailView.as_view(), name='card_detail')`

#### 3. card_detail.html — new template

**File**: `flashcards/templates/flashcards/card_detail.html`

**Intent**: Display card question, answer, topic name (or "—" if unset), and a "Back to list" link. When `can_edit` is `True`, show Edit and Delete action buttons.

#### 4. card_list.html — link each card tile to detail

**File**: `flashcards/templates/flashcards/card_list.html`

**Intent**: Wrap each card's `<div class="card ...">` in an anchor tag pointing to the card's detail URL so the tile is navigable.

**Contract**: `href="{% url 'flashcards:card_detail' card.pk %}"` on each card tile.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards` passes

#### Manual Verification

- Card list: clicking a card navigates to `/flashcards/<pk>/`
- Detail page shows question, answer, and topic
- Logged-in as owner: Edit and Delete buttons are visible
- Logged-in as a different non-staff user: Edit and Delete buttons are hidden
- Logged-in as staff: Edit and Delete buttons visible even for orphaned (null-owner) cards

**Implementation Note**: After manual confirmation, proceed to Phase 3.

---

## Phase 3: Update & Delete

### Overview

Add a permission mixin, `CardUpdateView`, `CardDeleteView`, their URLs, and templates. Update `card_form.html` title to be dynamic.

### Changes Required

#### 1. Imports update

**File**: `flashcards/views.py`

**Intent**: Add `UpdateView`, `DeleteView` to `from django.views.generic import …`; add `PermissionDenied` from `django.core.exceptions`.

#### 2. CardEditPermissionMixin

**File**: `flashcards/views.py`

**Intent**: A mixin placed before the CBV base in MRO that overrides `get_object()` to raise `PermissionDenied` if the viewer is neither the card's owner nor staff. Cards with `created_by = NULL` always require staff because `None != request.user`.

**Contract**: Override `get_object(queryset=None)` → call `super().get_object(queryset)` → check `obj.created_by != self.request.user and not self.request.user.is_staff` → raise `PermissionDenied` if True → return `obj`.

#### 3. CardUpdateView

**File**: `flashcards/views.py`

**Intent**: CBV that pre-fills `CardForm` for the selected card and saves changes on POST. Redirects to the card's detail page on success.

**Contract**: `LoginRequiredMixin + CardEditPermissionMixin + UpdateView`, `model = Card`, `form_class = CardForm`, `template_name = 'flashcards/card_form.html'`. Override `get_success_url` to return `reverse_lazy('flashcards:card_detail', kwargs={'pk': self.object.pk})`.

#### 4. CardDeleteView

**File**: `flashcards/views.py`

**Intent**: CBV that shows a confirmation page and, on POST, deletes the card and redirects to the card list.

**Contract**: `LoginRequiredMixin + CardEditPermissionMixin + DeleteView`, `model = Card`, `template_name = 'flashcards/card_delete_confirm.html'`, `success_url = reverse_lazy('flashcards:card_list')`.

#### 5. URLs for Update and Delete

**File**: `flashcards/urls.py`

**Intent**: Register edit and delete paths alongside the detail path.

**Contract**:
- `path('<int:pk>/edit/', views.CardUpdateView.as_view(), name='card_edit')`
- `path('<int:pk>/delete/', views.CardDeleteView.as_view(), name='card_delete')`

#### 6. card_form.html — dynamic title

**File**: `flashcards/templates/flashcards/card_form.html`

**Intent**: Replace the hardcoded "Nowa fiszka" heading with a conditional on the `object` context variable (Django sets it to `None` for CreateView, the Card instance for UpdateView).

**Contract**: Replace the `<h2>` text with `{% if object %}Edytuj fiszkę{% else %}Nowa fiszka{% endif %}`. Apply the same swap to the `{% block title %}`.

#### 7. card_delete_confirm.html — new template

**File**: `flashcards/templates/flashcards/card_delete_confirm.html`

**Intent**: Confirmation page showing the card's question text, a POST form with a "Usuń" submit button, and a "Anuluj" link back to the card's detail page.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test flashcards` passes

#### Manual Verification

- Edit: click Edit on detail page → form pre-filled → save → back at detail with updated content
- Delete: click Delete → confirmation page shows card question → confirm → card removed, redirected to card list
- Permission guard: as non-owner non-staff, navigate directly to `/flashcards/<pk>/edit/` → 403
- Permission guard: as non-owner non-staff, navigate directly to `/flashcards/<pk>/delete/` → 403
- Staff override: staff can edit/delete any card including those with null owner

**Implementation Note**: After manual confirmation, the feature is complete.

---

## Testing Strategy

### Unit Tests

- `CardEditPermissionMixin`: owner can access, non-owner raises 403, staff bypasses, null owner requires staff

### Manual Testing Steps

1. Register two user accounts (A and B) plus a staff account
2. User A creates a card with a topic — verify topic saved, card appears in study session
3. User A: edit the card → save → verify changes persisted; delete → confirm → verify gone
4. User B: attempt `/flashcards/<pk>/edit/` on User A's card → expect 403
5. Staff: edit a seeded card (null owner) → expect success

## References

- Research: `context/changes/crud-gap-analysis/research.md`
- Card model: `flashcards/models.py:14-27`
- CardForm: `flashcards/forms.py:6-16`
- Existing CBV pattern: `flashcards/views.py:84-95`
- URL conf: `flashcards/urls.py:1-14`
- card_list template: `flashcards/templates/flashcards/card_list.html`
- card_form template: `flashcards/templates/flashcards/card_form.html`

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Data Foundation

#### Automated

- [x] 1.1 Migration generates cleanly (`makemigrations --check` exits 0) — bba204b
- [x] 1.2 Migration applies cleanly (`migrate` exits 0) — bba204b
- [x] 1.3 `uv run python manage.py test flashcards` passes — bba204b

#### Manual

- [x] 1.4 Topic dropdown visible at `/flashcards/create/` — bba204b
- [x] 1.5 Card created with topic appears in a study session for that topic — bba204b
- [x] 1.6 `Card.created_by` is set to the creating user after creation — bba204b

### Phase 2: Card Detail View

#### Automated

- [x] 2.1 `uv run python manage.py test flashcards` passes — a1bb705

#### Manual

- [x] 2.2 Clicking a card in the list navigates to `/flashcards/<pk>/` — a1bb705
- [x] 2.3 Detail page shows question, answer, and topic — a1bb705
- [x] 2.4 Owner sees Edit and Delete buttons on detail page — a1bb705
- [x] 2.5 Non-owner non-staff sees no Edit or Delete buttons — a1bb705
- [x] 2.6 Staff sees Edit and Delete on orphaned (null-owner) cards — a1bb705

### Phase 3: Update & Delete

#### Automated

- [x] 3.1 `uv run python manage.py test flashcards` passes

#### Manual

- [x] 3.2 Edit pre-fills form; save redirects to detail with updated content
- [x] 3.3 Delete shows confirmation page; confirm removes card and redirects to list
- [x] 3.4 Non-owner direct URL to `/edit/` returns 403
- [x] 3.5 Non-owner direct URL to `/delete/` returns 403
- [x] 3.6 Staff can edit/delete orphaned (null-owner) cards