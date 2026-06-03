---
id: testing-score-accuracy-session-hardening
roadmap_id: test-plan-phase-1
title: Score accuracy & session hardening — integration tests
status: implemented
created: 2026-06-03
updated: 2026-06-03
prd_refs: [FR-003, FR-004]
prerequisites: [complete-study-session]
---

# test-plan Phase 1: Score accuracy & session hardening

Add 7 integration tests and one view fix covering three previously unprotected risks from `context/foundation/test-plan.md §2`:

- **Risk #1** — `session_score` diverges from `CardReview` DB count (score accuracy)
- **Risk #2** — cross-card POST bypass creates unauthorized `CardReview` (injection guard)
- **Risk #3** — partial session state causes `KeyError → 500` (reliability hardening)

## Artifacts

- `plan.md` — implementation contract (7 tests + view fix across 3 phases)
- `plan-brief.md` — two-pager summary
- Oracle: `context/changes/complete-study-session/research.md §6 Luki testowe`
