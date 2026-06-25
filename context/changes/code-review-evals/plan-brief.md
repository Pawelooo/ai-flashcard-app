# Promptfoo Evaluation Suite for Code Reviewer — Plan Brief

> Full plan: `context/changes/code-review-evals/plan.md` Research: `context/changes/code-review-evals/research.md`

## What & Why

Add [promptfoo](https://promptfoo.dev) to `packages/code-reviewer` to run the existing AI code review prompt side-by-side against three OpenRouter models. The motivation is to answer: "are cheaper models (glm-5.1, deepseek-v4-flash) a viable substitute for the claude-sonnet-4-6 baseline currently used in CI?"

## Starting Point

`packages/code-reviewer` already has a working TypeScript reviewer with a clean input/output contract (6-criterion Zod schema, env-driven model selection via `OPENROUTER_MODEL`). There are no tests, no fixtures, and no promptfoo config — everything in this plan is net-new.

## Desired End State

Running `npm run eval` from `packages/code-reviewer/` produces a side-by-side promptfoo report showing all three models scored against a single Django diff. Two assertions per run reveal which models correctly identify the three embedded flaws.

## Key Decisions Made

Decision

Choice

Why (1 sentence)

Source

Integration pattern

Custom TS provider (not `exec` subprocess)

Avoids env-var gymnastics; typed imports of existing schema/prompt

Research

Models to compare

claude-sonnet-4-6 + z-ai/glm-5.1 + deepseek/deepseek-v4-flash

Baseline needed to judge whether cheaper models are "good enough"

Plan Q&A

Fixture domain

Django (`UserCardStatsView` in flashcards app)

Project is Django/Python — React diff would be unrealistic for this codebase

User

Fixture flaws

auth missing + DoesNotExist unhandled + count()>0 vs exists()

Each flaw targets a distinct criterion (security, correctness, idiomaticity)

Plan Q&A

Static assertion

`aggregate_score ≤ 6`

Deterministic, model-independent check that the flawed diff scores below CI pass threshold

Plan Q&A

LLM judge

claude-sonnet-4-6 via OpenRouter

No new provider setup; self-scoring bias acceptable here because judge verifies facts not quality

Plan Q&A

maxTokens in evals

4096 (vs. 2048 in CI)

Complex diff + 6 criteria with rationales risks truncation at 2048

Research → Plan

## Scope

**In scope:**

-   `promptfoo` dev dependency + `eval` npm script in `packages/code-reviewer/package.json`
-   `evals/fixtures/django-card-stats.diff` — unified diff with three deliberate flaws
-   `src/agent.ts` factory function `createCodeReviewerAgent(model, opts?)` (backward-compatible)
-   `evals/provider.ts` — custom promptfoo provider using factory + existing prompts/schema
-   `promptfooconfig.yaml` — 3 providers × 1 test case × 2 assertions

**Out of scope:**

-   Modifying `src/main.ts` or the CI workflow
-   Multiple fixtures or fixtures in other languages
-   Snapshot/golden-file tests (output is non-deterministic)
-   Network mocking or offline mode

## Architecture / Approach

The promptfoo custom TypeScript provider pattern (`file://evals/provider.ts`) replaces the `exec` subprocess approach. The provider reuses `createCodeReviewerAgent(model)` and `buildUserPrompt` from `src/`, creates a fresh agent per invocation with the model from `context.provider.config.model`, reads the diff file from `context.vars.diff_file`, and returns `{ output: JSON.stringify({...}) }` with the full review JSON.

```
promptfooconfig.yaml
  └─ provider: file://evals/provider.ts (× 3 model labels)
        └─ createCodeReviewerAgent(model, { maxTokens: 4096 })
              └─ OpenRouter → model
        └─ buildUserPrompt(title, description, diff)
        └─ returns ReviewResult JSON
  └─ tests[0].vars → diff_file, PR_TITLE
  └─ tests[0].assert → JS (aggregate_score ≤ 6) + llm-rubric (3 flaws)
```

## Phases at a Glance

Phase

What it delivers

Key risk

1. Install & scaffold

promptfoo installed, `evals/` dir exists, `npm run eval` script wired

peer-dep conflict with ai@^6 or zod@^4

2. Django diff fixture

`django-card-stats.diff` with 3 verifiable flaws

hunk offsets computed incorrectly → `git apply --check` fails

3. Agent factory + provider

`createCodeReviewerAgent` factory, `evals/provider.ts`

agent.ts singleton regression; TypeScript module resolution edge case

4. Config + end-to-end

`promptfooconfig.yaml`, `npm run eval` runs and prints table

OpenRouter model ID strings incorrect; promptfoo template parser rejects YAML

**Prerequisites:** `OPENROUTER_API_KEY` available in `../../.env` (already required for CI — no new secret). **Estimated effort:** ~1 session across 4 phases.

## Open Risks & Assumptions

-   `z-ai/glm-5.1` and `deepseek/deepseek-v4-flash` must be valid OpenRouter model IDs at run time — verify at `openrouter.ai/models` before Phase 4.
-   promptfoo's esbuild-based TS compilation must handle `moduleResolution: "Bundler"` from the existing `tsconfig.json` — if not, a minimal `tsconfig.eval.json` override for `evals/` is the fallback.
-   The LLM-as-a-judge pass/fail threshold for the rubric is qualitative; a model that mentions two out of three flaws may still pass. This is acceptable for a first eval run.

## Success Criteria (Summary)

-   `npm run eval` produces a CLI table with 3 model columns and 1 test row.
-   At least one model row shows `aggregate_score ≤ 6` on the flawed diff.
-   `npm start` with the same fixture diff still emits valid JSON (CI path unaffected).