<!-- PLAN-REVIEW-REPORT -->
# Plan Review: K1 Session key typed wrapper

- **Plan**: `context/changes/refactor-opportunities/plan.md`
- **Mode**: Deep
- **Date**: 2026-06-14
- **Verdict**: REVISE
- **Findings**: 0 critical | 1 warning | 1 observation

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| End-State Alignment | PASS |
| Lean Execution | PASS |
| Architectural Fitness | PASS |
| Blind Spots | WARNING |
| Plan Completeness | WARNING |

## Grounding

5/5 paths ✓ (`flashcards/views.py`, `flashcards/tests.py`, `flashcards/session.py` new, `stats/types.py`, `flashcards/management/commands/verify_manual_checks.py`), 3/3 symbols ✓ (`_SESSION_KEYS` at lines 16, 32, 80; study_card line numbers 167/171-172/187/189/191/193 confirmed), brief↔plan ✓.

## Findings

### F1 — verify_manual_checks.py has 2 uncovered session key literals

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots
- **Location**: Scope boundaries + Phase 5 success criteria
- **Detail**: `flashcards/management/commands/verify_manual_checks.py:71` and `:167` both access `client.session["session_cards"]` via string literal. The plan doesn't mention this file in scope or in "What We're NOT Doing." Phase 5's automated success criterion `grep -n '"session_' flashcards/views.py flashcards/tests.py` only checks those two files — it gives a green signal even with two literals still live in verify_manual_checks.py.
- **Fix A ⭐ Recommended**: Add verify_manual_checks.py to Phase 5 scope. 2 replacements (`"session_cards"` → `SK.CARDS` at lines 71, 167) + 1 import. Update the grep to cover all `flashcards/` .py files.
  - Strength: Codebase is fully consistent after the refactor — no surviving string literals anywhere in flashcards/.
  - Tradeoff: Phase 5 scope grows by ~3 lines.
  - Confidence: HIGH — trivial change, management command is low-risk.
  - Blind spot: None significant.
- **Fix B**: Explicitly scope out verify_manual_checks.py. Add to "What We're NOT Doing": management command literals. Keep grep as-is (targeted to views.py + tests.py).
  - Strength: Plan stays scoped; management command is test tooling, not production.
  - Tradeoff: Two string literals survive; future grep checks need to remember the exclusion.
  - Confidence: HIGH — the command is non-production tooling.
  - Blind spot: None significant.
- **Decision**: PENDING

### F2 — Phase 5 study_card contract omits line 189 read of session_wrong_ids

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Completeness
- **Location**: Phase 5 — study_card contract, Reads section
- **Detail**: The contract says "Reads (lines 171-172)" and lists session_cards and session_index. There is a third session read at line 189: `wrong = request.session['session_wrong_ids']`. This falls inside the "Writes (lines 187-193)" range in the contract where it is categorised as a write — but line 189 is a READ. An implementer following the contract literally could leave line 189 as a string literal.
- **Fix**: Extend reads section to "(lines 171-172, 189)" and note that `state[SK.WRONG_IDS]` replaces `request.session['session_wrong_ids']` at line 189.
- **Decision**: PENDING