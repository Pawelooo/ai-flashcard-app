


<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Card CRUD Completion

- **Plan**: `context/changes/crud-gap-analysis/plan.md`
- **Scope**: All phases (1–3 of 3)
- **Date**: 2026-06-11
- **Verdict**: NEEDS ATTENTION
- **Findings**: 0 critical security issues, 1 critical testing gap, 5 warnings, 2 observations

## Verdicts

| Dimension | Verdict |
|---|---|
| Plan Adherence | WARNING — 1 cosmetic drift in card_form.html block title |
| Scope Discipline | PASS — incidental pre-commit/lint fixes bundled with justification |
| Safety & Quality | WARNING — permission logic correct, but mixin has zero test coverage |
| Architecture | PASS |
| Pattern Consistency | WARNING — success_url style gap (justified but undocumented) |
| Success Criteria | PASS — all automated checks pass, all manual items confirmed |

## Findings

### F1 — CardEditPermissionMixin has zero test coverage

- **Severity**: ❌ CRITICAL
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: `flashcards/tests.py` (absent)
- **Detail**: The permission mixin is the security-critical path of this feature — it controls who can edit and delete cards. Eight cases are completely untested: owner can edit/delete, non-owner gets 403 on both views, staff overrides on both views, null-owner is staff-only on both views. Any regression in `CardEditPermissionMixin.get_object()` would be invisible to CI.
- **Fix**: Add a `CardPermissionTests` test class covering: (1) owner can GET/POST `/edit/` and `/delete/`; (2) non-owner gets 403 on both; (3) staff user passes for another user's card; (4) null `created_by` card → 403 for regular user, passes for staff.
  - Strength: Covers the exact four-case contract the plan specified in "Testing Strategy". Closes the gap before any future refactor can silently break it.
  - Tradeoff: ~30–40 lines of test code.
  - Confidence: HIGH — contract is fully specified in the plan.
  - Blind spot: None significant.
- **Decision**: FIXED — Added CardPermissionTests (12 cases) in flashcards/tests.py

### F2 — No tests for CardDetailView

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `flashcards/tests.py` (absent)
- **Detail**: `CardDetailView` has no test coverage. Missing: authenticated user can GET `/flashcards/<pk>/` → 200; unauthenticated user is redirected; `can_edit` is True for owner/staff and False for non-owner.
- **Fix**: Add `CardDetailViewTests` with 3–4 assertions.
- **Decision**: FIXED — Added CardDetailViewTests (5 cases) in flashcards/tests.py

### F3 — No tests for CardUpdateView form behavior

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `flashcards/tests.py` (absent)
- **Detail**: Missing: GET pre-fills form with existing card data; valid POST updates and redirects to detail; invalid POST (blank question) returns 200 with form errors.
- **Fix**: Add `CardUpdateViewTests` with 3 cases.
- **Decision**: FIXED — Added CardUpdateViewTests (3 cases) in flashcards/tests.py

### F4 — No tests for CardDeleteView

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `flashcards/tests.py` (absent)
- **Detail**: Missing: POST deletes the card and redirects to card list; card no longer exists in DB after deletion.
- **Fix**: Add `CardDeleteViewTests` with 2 cases.
- **Decision**: FIXED — Added CardDeleteViewTests (2 cases) in flashcards/tests.py

### F5 — No select_related on CardListView — latent N+1

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `flashcards/views.py:85`
- **Detail**: `CardListView` issues `SELECT * FROM flashcards_card` with no `select_related`. The current template doesn't access `card.topic` in the list loop, so no N+1 today. But `CardDetailView` renders topic, and any future extension showing the topic badge per tile in the list would silently introduce N+1.
- **Fix**: Override `get_queryset` on `CardListView` to add `.select_related('topic', 'created_by')`. One-liner.
- **Decision**: FIXED — Added get_queryset with select_related to CardListView in flashcards/views.py

### F6 — Null-owner permission relies on implicit Python semantics — no comment

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Pattern Consistency
- **Location**: `flashcards/views.py:106`
- **Detail**: The line `if obj.created_by != self.request.user and not self.request.user.is_staff:` relies on `None != <User object>` always being True in Python. This is correct but non-obvious to a future reader unfamiliar with the intent. A comment stating the null-owner contract would prevent accidental "fixes" that break it.
- **Fix**: Add `# None != any User, so cards without an owner are staff-only` above line 106.
- **Decision**: FIXED — Added null-owner comment above the permission check in flashcards/views.py

### F7 — card_form.html browser-tab title says "Dodaj fiszkę", heading says "Nowa fiszka"

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: `flashcards/templates/flashcards/card_form.html:2`
- **Detail**: The plan specified `"Nowa fiszka"` in both the `{% block title %}` and `<h2>`. The `<h2>` is correct. But the `{% block title %}` else-branch renders `"Dodaj fiszkę"` — so the browser tab says "Dodaj fiszkę" while the page heading says "Nowa fiszka" during card creation. Cosmetic only.
- **Fix**: Change `{% else %}Dodaj fiszkę{% endif %}` to `{% else %}Nowa fiszka{% endif %}` in the `{% block title %}` block (line 2).
- **Decision**: FIXED — Changed {% block title %} else-branch from "Dodaj fiszkę" to "Nowa fiszka" in card_form.html

### F8 — CardUpdateView uses get_success_url() while siblings use success_url attribute

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Pattern Consistency
- **Location**: `flashcards/views.py:116`
- **Detail**: `CardCreateView` and `CardDeleteView` use `success_url = reverse_lazy(...)` as a class attribute. `CardUpdateView` uses `get_success_url()` as a method. The difference is justified (`CardUpdateView` needs `self.object.pk`), but a reader might wonder why it's inconsistent without a comment.
- **Fix**: Add `# success_url can't be a class attribute here — URL requires self.object.pk` as a comment.
- **Decision**: FIXED — Added comment above get_success_url() in CardUpdateView in flashcards/views.py