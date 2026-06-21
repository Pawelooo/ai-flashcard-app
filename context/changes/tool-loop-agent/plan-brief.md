# tool-loop-agent — Plan Brief

> Full plan: `context/changes/tool-loop-agent/plan.md`

## What & Why

Migrate `packages/code-reviewer/src/main.py` from a single-file Python script to a modular TypeScript module built on the Vercel AI SDK `ToolLoopAgent`. The goal is a reusable, typed agent that can be imported directly in promptfoo evals in a future change.

## Starting Point

A single Python file (`main.py`) with all concerns mixed: Pydantic schema, system prompt inline in the API call, OpenAI client factory, and review function. The package already has JS dependencies installed (`ai`, `@openrouter/ai-sdk-provider`, `zod`) but no TypeScript configuration or `.ts` files.

## Desired End State

`npm start` in `packages/code-reviewer/` runs `src/main.ts` via tsx and prints the same structured review output as the current Python script. A named export `codeReviewerAgent` from `src/agent.ts` can be imported by promptfoo evals without any AI SDK boilerplate. `main.py` remains unchanged.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| Language | TypeScript | `ToolLoopAgent` is a TS-first API — no Python equivalent | Plan |
| Provider | OpenRouter | Already installed + `OPENROUTER_API_KEY` in .env — zero config change | Plan |
| TS runner | tsx | Zero-config, no build step, works with CommonJS | Plan |
| Eval export | Named agent instance | `codeReviewerAgent.generate()` is the direct promptfoo contract | Plan |
| Schema | 1:1 Zod conversion | Keeps migration scope minimal, easy to verify correctness | Plan |
| main.py | Leave untouched | Two parallel environments in one package — no regression risk | Plan |

## Scope

**In scope:** `tsconfig.json`, `tsx` devDependency, `src/schemas/review.ts`, `src/prompts/review.ts`, `src/agent.ts`, `src/main.ts`

**Out of scope:** promptfoo eval config, additional review tools, streaming endpoint, CI changes, any changes to Python files

## Architecture / Approach

Leaf-up: schemas module has no dependencies, prompts module has no dependencies, agent module imports both, main entrypoint imports agent + prompts. `ToolLoopAgent` is configured with `Output.object({ schema: reviewResultSchema })` for structured output — no tools needed for this use case.

```
main.ts → agent.ts → schemas/review.ts
       ↘ prompts/review.ts ↗
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. TypeScript Setup | tsconfig.json + tsx + npm scripts | `"type": "commonjs"` in package.json must align with tsconfig `module` setting |
| 2. Schema Module | Zod ReviewResult — typed source of truth | Zod v4 constraint API differs from v3 — verify `.int().min().max()` chain |
| 3. Prompts Module | Typed system prompt + user prompt builder | Prompt strings must match Python verbatim for baseline parity |
| 4. Agent Module | `codeReviewerAgent` export + `CodeReviewerUIMessage` type | `Output.object` + `InferAgentUIMessage` integration with OpenRouter provider |
| 5. Main Entrypoint | `npm start` produces same output as `python src/main.py` | API key must be present in env |

**Prerequisites:** `OPENROUTER_API_KEY` in `.env`, Node.js installed  
**Estimated effort:** ~1 session across 5 phases

## Open Risks & Assumptions

- Zod v4 (installed as `zod@^4.4.3`) has a different API for some constraints vs v3 — implementer must verify against installed source, not memory.
- `ToolLoopAgent` without tools for pure structured output is supported per docs, but not the primary advertised use case — confirm behaviour with `Output.object` only.

## Success Criteria (Summary)

- `npm start` exits 0 and prints review output for the sample code snippet
- `import { codeReviewerAgent } from './src/agent'` works in a Node.js context without errors
- All five new files have zero TypeScript errors in IDE