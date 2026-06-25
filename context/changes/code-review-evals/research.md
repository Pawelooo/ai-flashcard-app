---
date: 2026-06-25T00:00:00+00:00
researcher: Pawelooo
git_commit: 45664289e1e8944b02c9fe7740997d2fc397cfb2
branch: master
repository: ai-flashcard-app
topic: "Promptfoo evaluation suite for the AI code reviewer agent"
tags: [research, code-reviewer, promptfoo, evals, openrouter, multi-model]
status: complete
last_updated: 2026-06-25
last_updated_by: Pawelooo
---

# Research: Promptfoo evaluation suite for the AI code reviewer agent

**Date**: 2026-06-25
**Researcher**: Pawelooo
**Git Commit**: 45664289e1e8944b02c9fe7740997d2fc397cfb2
**Branch**: master
**Repository**: ai-flashcard-app

## Research Question

Analyze the current state of `packages/code-reviewer` in the context of introducing promptfoo evaluations. Assess reusability of prompts, importability of the agent, and alignment of the tech stack with promptfoo. Goal: test the same code review prompt on three models (z-ai/glm-5.1, deepseek/deepseek-v4-flash, and the baseline claude-sonnet-4-6) using a single complex React 16→19 migration diff with three known flaws, evaluated with LLM-as-a-judge and a static pass/fail check.

## Summary

The existing `packages/code-reviewer` stack is **well-aligned with promptfoo**. All key pieces (system prompt, buildUserPrompt, Zod schema, agent) are exported and importable. The `OPENROUTER_MODEL` env var already enables zero-code model switching across the three target models — all of which are available on OpenRouter. No `.diff` test fixtures or promptfoo config exist yet; both need to be created. The integration path is clean: either a custom promptfoo TypeScript provider (direct agent import) or an `exec` provider (CLI subprocess). The LLM-as-a-judge and static test patterns are both straightforward given the structured JSON output.

## Detailed Findings

### Input/Output Contract

The reviewer's public interface is fully env-driven:

| Env var | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | yes | OpenRouter auth |
| `OPENROUTER_MODEL` | no | Model override (default: `anthropic/claude-sonnet-4-6`) |
| `DIFF_FILE` | yes | Path to file containing the raw git diff |
| `PR_TITLE` | yes | PR title string |
| `PR_DESCRIPTION` | no | PR description (omitted if empty) |

stdout emits a single JSON line:
```json
{
  "criteria": {
    "implementation_correctness": { "score": 1–10, "rationale": "..." },
    "idiomaticity":               { "score": 1–10, "rationale": "..." },
    "complexity":                 { "score": 1–10, "rationale": "..." },
    "test_coverage":              { "score": 1–10, "rationale": "..." },
    "documentation":              { "score": 1–10, "rationale": "..." },
    "security_and_safety":        { "score": 1–10, "rationale": "..." }
  },
  "aggregate_score": <mean of 6 scores, rounded to 1 decimal>,
  "summary": "2–4 sentence assessment",
  "issues": ["..."]
}
```

- `packages/code-reviewer/src/main.ts:1–33` — entry point
- `packages/code-reviewer/src/schemas/review.ts:1–23` — Zod schema (`reviewResultSchema`, `ReviewResult`)
- `packages/code-reviewer/src/prompts/review.ts:1–52` — `SYSTEM_PROMPT`, `buildUserPrompt`
- `packages/code-reviewer/src/agent.ts:1–15` — `codeReviewerAgent` (ToolLoopAgent, OpenRouter)

### Promptfoo Stack Alignment

| Layer | Current state | Promptfoo compatibility |
|---|---|---|
| Language | TypeScript (tsx, strict) | ✅ promptfoo has first-class TS support |
| Runtime | Node.js (commonjs, tsx@4) | ✅ promptfoo runs in Node |
| Output validation | Zod (`reviewResultSchema`) | ✅ can drive promptfoo `assert` targets |
| Model provider | OpenRouter (`@openrouter/ai-sdk-provider`) | ✅ OpenRouter hosts all 3 target models |
| Model switching | `OPENROUTER_MODEL` env var | ✅ maps directly to promptfoo `providers[]` env override |
| Agent exportability | `codeReviewerAgent` exported from `agent.ts` | ✅ importable as a custom provider |
| Prompt exportability | `SYSTEM_PROMPT` + `buildUserPrompt` exported | ✅ reusable in promptfoo config |
| Existing evals | None | ⬜ everything needs to be created |
| Existing `.diff` fixtures | None | ⬜ React 16→19 diff must be authored |

### Multi-Model Testing Path

All three target models are available on OpenRouter. No code changes required — switching models is a matter of setting `OPENROUTER_MODEL` in the promptfoo provider config:

- `anthropic/claude-sonnet-4-6` — current baseline (default in `agent.ts:9`)
- `z-ai/glm-5.1` — target model 1
- `deepseek/deepseek-v4-flash` — target model 2

The promptfoo `providers[]` array can declare these as three variants of the same provider, each differing only in the env override.

### Two Viable Integration Approaches

**Option A — Custom TypeScript provider (import)**

Promptfoo supports a custom provider defined as a `.ts` file. The provider would:
1. Import `codeReviewerAgent` from `packages/code-reviewer/src/agent.ts`
2. Import `buildUserPrompt` from `packages/code-reviewer/src/prompts/review.ts`
3. Accept the diff + PR title as promptfoo vars
4. Call `codeReviewerAgent.generate()` and return `output`

Advantage: typed, fast, no subprocess overhead, errors surface cleanly.
Limitation: the provider needs to instantiate a new `ToolLoopAgent` per model variant (since `agent.ts` creates the agent at module load with a fixed env var). Requires a thin factory wrapper.

**Option B — `exec` provider (subprocess)**

Promptfoo's `exec` provider runs `npx tsx src/main.ts` as a subprocess, passing env vars per invocation. No code changes to the reviewer.

Advantage: zero coupling — exercises the exact CI entrypoint.
Limitation: subprocess startup latency (~1–2s per call), harder to get structured errors.

**Recommendation: Option B** for the first evaluation suite. It tests the real CI path without any wiring code, and the latency is acceptable for an offline eval run. If eval speed becomes a concern, migrate to Option A.

### Agent Internals

- `packages/code-reviewer/src/agent.ts` uses `ToolLoopAgent` from `ai@^6.0.207` with `Output.object({ schema: reviewResultSchema })` — structured output is enforced at the SDK level.
- `maxTokens: 2048` — sufficient for a complex diff + 6 criteria with rationales.
- The Zod schema (`schemas/review.ts:3–6`) captures `rationale: string` per criterion — these rationales are the primary surface for LLM-as-a-judge to verify flaw identification.

### CI/CD Integration (context)

The composite action (`.github/actions/ai-code-review/action.yml`) already uses the same env-driven interface. The eval suite is additive — it does not touch the action.

### What Does Not Exist Yet

- No `promptfooconfig.yaml` or any promptfoo setup anywhere in the repo
- No `.diff` test fixtures — the React 16→19 migration diff with 3 flaws needs to be authored
- No test runner in `packages/code-reviewer/package.json` (`"test"` script is a placeholder)

## Code References

- `packages/code-reviewer/src/agent.ts:1–15` — ToolLoopAgent, OPENROUTER_MODEL env var, maxTokens
- `packages/code-reviewer/src/schemas/review.ts:1–23` — Zod schema, ReviewResult type
- `packages/code-reviewer/src/prompts/review.ts:1–52` — SYSTEM_PROMPT with rubrics, buildUserPrompt
- `packages/code-reviewer/src/main.ts:1–33` — env var interface, aggregate_score computation, stdout JSON
- `packages/code-reviewer/package.json:7` — `"start": "tsx --env-file=../../.env src/main.ts"`
- `.github/actions/ai-code-review/action.yml` — composite action (diff extraction, model invocation, comment/label management)
- `.github/workflows/code-review.yml` — workflow triggers, base-ref passing

## Architecture Insights

1. **`OPENROUTER_MODEL` is the multi-model toggle** — no code changes needed to switch models in evals. This was an intentional design decision in the ci-cd change.
2. **Aggregate score is computed in TypeScript, not by the model** — it's deterministic (`main.ts:20`). Static assertions on aggregate_score are reliable.
3. **Each criterion includes a `rationale` string** — this is the LLM-as-a-judge's primary input: check whether the rationale mentions the specific known flaws in the test diff.
4. **`ToolLoopAgent` wraps the model** — it's not a plain completion call. The structured output contract is enforced by the SDK's `Output.object()` wrapper, which means malformed JSON from the model is caught before it reaches stdout.

## Historical Context (from prior changes)

- `context/changes/ci-cd/plan.md` — full implementation history; key decision: `OPENROUTER_MODEL` env var added for model flexibility (`plan.md:104`); TLS workaround removed for GHA compatibility (`plan.md:48`); aggregate computed in TS not by model (`plan.md:52`)
- `context/changes/ci-cd/requirements.md` — the 6 scoring criteria with 1/10 anchors; these are the rubrics already embedded in `SYSTEM_PROMPT`; the evaluation suite should verify that the model applies these rubrics correctly

## Open Questions

1. **React 16→19 diff authoring**: What are the three specific flaws to embed? Candidates: (a) legacy lifecycle method (`componentWillMount` → `useEffect`), (b) string ref → `createRef`/`useRef`, (c) missing key prop in a list render. These produce real implementation_correctness and security_and_safety signals.
2. **LLM-as-a-judge model**: Which model judges the output? Using the same model as the reviewer introduces self-scoring bias. A separate judge model (e.g., claude-opus-4-8) is preferable.
3. **Pass threshold for evals**: The CI threshold is `aggregate_score >= 7`. For evals on a diff with 3 known flaws, the expected score should be lower — define the expected range (e.g., `aggregate_score <= 6`) as the static assertion.
4. **Promptfoo version**: Check npm for the latest `promptfoo` version compatible with Node.js 20 and the `exec` provider pattern before pinning in `package.json`.
5. **Token budget**: 2048 tokens may be tight for a complex React 16→19 diff + 6 criteria with rationales. Consider raising `maxTokens` in `agent.ts` for eval runs.
