# tool-loop-agent Implementation Plan

## Overview

Convert `packages/code-reviewer/src/main.py` from a single-file Python script (OpenAI SDK + Pydantic) into a modular TypeScript module built on the Vercel AI SDK `ToolLoopAgent`. The result is a reusable, typed agent that can be imported directly in promptfoo evals.

## Current State Analysis

`packages/code-reviewer/src/main.py` contains everything in one file: a Pydantic `ReviewResult` schema, a hard-coded system prompt inside the API call, an `OpenAI` client factory, and a `review_code()` function. The package already has the JS dependencies needed for the migration:
- `ai@^6.0.207` — Vercel AI SDK with `ToolLoopAgent`, `Output`, `InferAgentUIMessage`
- `@openrouter/ai-sdk-provider@^2.9.1` — OpenRouter provider (`createOpenRouter`)
- `zod@^4.4.3` — schema library (Pydantic equivalent)

No TypeScript configuration exists yet. `main.py` stays untouched throughout this change.

## Desired End State

```
packages/code-reviewer/
  src/
    schemas/
      review.ts       # Zod ReviewResult schema + TypeScript type
    prompts/
      review.ts       # system prompt + user prompt template
    agent.ts          # ToolLoopAgent instance export + InferAgentUIMessage type
    main.ts           # demo entrypoint (mirrors current main.py behaviour)
    main.py           # unchanged
  tsconfig.json
  package.json        # tsx added to devDependencies, start script added
```

Running `npm start` executes `main.ts` and prints the same review output as the current Python script.

### Key Discoveries

- `ToolLoopAgent` accepts `output: Output.object({ schema })` for structured output without requiring tools — the code reviewer needs no tools.
- `@openrouter/ai-sdk-provider` exports `createOpenRouter(options)` — API key passed via `options.apiKey` from `process.env.OPENROUTER_API_KEY`.
- `InferAgentUIMessage<typeof agent>` gives promptfoo/UI consumers a typed message shape.
- `tsx` runs TypeScript directly without a build step — zero-config for dev and eval use.
- `zod@4` (already installed) uses `z.number().int()` not `.int().min()` — check exact constraints against installed version.

## What We're NOT Doing

- No promptfoo eval configuration — that's a separate change.
- No changes to `main.py` or `pyproject.toml`.
- No additional review tools (web search, AST analysis, etc.) — ToolLoopAgent with no tools.
- No streaming endpoint or UI integration.
- No CI changes.

## Implementation Approach

Five sequential phases: TypeScript environment first, then leaf modules (schemas → prompts), then the agent that consumes them, then the demo entrypoint. Each phase has a single, testable deliverable.

---

## Phase 1: TypeScript Setup

### Overview

Bootstrap TypeScript in the package so subsequent phases can be written and executed as `.ts` files.

### Changes Required

#### 1. `tsconfig.json`

**File**: `packages/code-reviewer/tsconfig.json`

**Intent**: Minimal TypeScript config targeting Node.js CommonJS output (matching the existing `"type": "commonjs"` in `package.json`).

**Contract**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

#### 2. `package.json` — add tsx and scripts

**File**: `packages/code-reviewer/package.json`

**Intent**: Add `tsx` as a devDependency and a `start` script so `npm start` runs `src/main.ts` directly via tsx.

**Contract**: Add to `devDependencies`: `"tsx": "^4.0.0"`. Add to `scripts`: `"start": "tsx src/main.ts"`.

### Success Criteria

#### Automated Verification

- `npx tsx --version` exits 0 in the `packages/code-reviewer/` directory after `npm install`
- `npx tsc --noEmit` exits 0 (no type errors, no files yet — just config validation)

#### Manual Verification

- `npm install` completes without errors in `packages/code-reviewer/`

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Phase 2: Schema Module

### Overview

Extract the `ReviewResult` structure from Python's Pydantic model into a Zod schema, making it the single source of truth for the TypeScript side.

### Changes Required

#### 1. `src/schemas/review.ts`

**File**: `packages/code-reviewer/src/schemas/review.ts`

**Intent**: Define and export the `reviewResultSchema` Zod object (1:1 equivalent of Python's `ReviewResult`) and its inferred TypeScript type `ReviewResult`.

**Contract**:
- `summary`: `z.string()`
- `issues`: `z.array(z.string())`
- `score`: `z.number().int()` with min 1, max 10 constraint — verify exact Zod v4 API against installed version
- Export both `reviewResultSchema` and `type ReviewResult`

### Success Criteria

#### Automated Verification

- `npx tsc --noEmit` exits 0 after creating this file
- `npx tsx src/schemas/review.ts` exits 0 (no runtime errors on import)

#### Manual Verification

- Schema file exports are importable and `ReviewResult` type is visible in IDE autocomplete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Phase 3: Prompts Module

### Overview

Extract the system prompt and user prompt template from the inline `messages` array in `main.py` into typed string exports.

### Changes Required

#### 1. `src/prompts/review.ts`

**File**: `packages/code-reviewer/src/prompts/review.ts`

**Intent**: Export the system prompt string and a `buildUserPrompt(code: string): string` function that produces the user message, both derived from the hardcoded strings in `main.py`.

**Contract**:
- `export const SYSTEM_PROMPT: string` — value: `"You are a code reviewer. Analyse the provided code and return structured feedback."`
- `export function buildUserPrompt(code: string): string` — returns `` `Review this code:\n\n${code}` ``

### Success Criteria

#### Automated Verification

- `npx tsc --noEmit` exits 0
- `npx tsx src/prompts/review.ts` exits 0

#### Manual Verification

- Prompt constants match the strings in `main.py` exactly

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Phase 4: Agent Module

### Overview

Create the reusable `ToolLoopAgent` instance that consumes the schema and prompts modules, and export it along with its inferred UI message type.

### Changes Required

#### 1. `src/agent.ts`

**File**: `packages/code-reviewer/src/agent.ts`

**Intent**: Instantiate `ToolLoopAgent` with the OpenRouter provider, `Output.object` structured output using `reviewResultSchema`, and the system prompt. Export the agent instance as `codeReviewerAgent` and export `CodeReviewerUIMessage` for future UI/eval consumers.

**Contract**:
- Import `ToolLoopAgent`, `Output`, `InferAgentUIMessage` from `'ai'`
- Import `createOpenRouter` from `'@openrouter/ai-sdk-provider'`
- Import `reviewResultSchema` from `'./schemas/review'`
- Import `SYSTEM_PROMPT` from `'./prompts/review'`
- Create OpenRouter provider: `const openrouter = createOpenRouter({ apiKey: process.env.OPENROUTER_API_KEY })`
- Default model: `'openai/gpt-4o-mini'` (matches `main.py`)
- Agent config: `instructions: SYSTEM_PROMPT`, `output: Output.object({ schema: reviewResultSchema })`
- `export const codeReviewerAgent` — the `ToolLoopAgent` instance
- `export type CodeReviewerUIMessage = InferAgentUIMessage<typeof codeReviewerAgent>`

### Success Criteria

#### Automated Verification

- `npx tsc --noEmit` exits 0
- `npx tsx src/agent.ts` exits 0 (no errors on module load; agent is not invoked)

#### Manual Verification

- `codeReviewerAgent` is importable in a REPL or eval context without errors
- TypeScript IDE shows `output` typed as `ReviewResult` on `agent.generate()` result

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Phase 5: Main Entrypoint

### Overview

Create `src/main.ts` as the demo entrypoint that mirrors `main.py` — reviews the same sample code and prints the same fields.

### Changes Required

#### 1. `src/main.ts`

**File**: `packages/code-reviewer/src/main.ts`

**Intent**: Import `codeReviewerAgent` and `buildUserPrompt`, call `agent.generate()` with the same sample snippet used in `main.py`, and print `summary`, `score`, and `issues` to stdout in the same format.

**Contract**:
- Same sample code string as `main.py` (the `add(a, b)` snippet with type mismatch)
- Call: `const { output } = await codeReviewerAgent.generate({ prompt: buildUserPrompt(sample) })`
- Print format mirrors Python's `Summary :`, `Score :`, `Issues :` output
- Wrap in async `main()` called at bottom: `main().catch(console.error)`

### Success Criteria

#### Automated Verification

- `npx tsc --noEmit` exits 0
- `npm start` exits 0 with `OPENROUTER_API_KEY` set

#### Manual Verification

- `npm start` prints a summary, score (1-10), and at least one issue for the sample code
- Output format mirrors the Python script's output
- No TypeScript errors in IDE on any of the five new files

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Testing Strategy

### Manual Testing Steps

1. Set `OPENROUTER_API_KEY` in `.env` (already present from Python setup)
2. Run `npm install` in `packages/code-reviewer/`
3. Run `npm start` — verify output matches structure of `python src/main.py`
4. In a REPL or test file, `import { codeReviewerAgent } from './src/agent'` — verify it loads without errors
5. Check that `output` from `agent.generate()` is typed as `ReviewResult` in the IDE

## References

- AI SDK ToolLoopAgent docs: `packages/code-reviewer/node_modules/ai/docs/03-agents/02-building-agents.mdx`
- Type-safe agents reference: `packages/code-reviewer/.agents/skills/ai-sdk/references/type-safe-agents.md`
- OpenRouter provider: `packages/code-reviewer/node_modules/@openrouter/ai-sdk-provider/dist/index.d.ts:830`
- Source: `packages/code-reviewer/src/main.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: TypeScript Setup

#### Automated

- [x] 1.1 `npx tsx --version` exits 0 after npm install — 911495b
- [x] 1.2 `npx tsc --noEmit` exits 0 — 911495b

#### Manual

- [x] 1.3 `npm install` completes without errors — 911495b

### Phase 2: Schema Module

#### Automated

- [x] 2.1 `npx tsc --noEmit` exits 0 — 577f1ca
- [x] 2.2 `npx tsx src/schemas/review.ts` exits 0 — 577f1ca

#### Manual

- [x] 2.3 `ReviewResult` type visible in IDE autocomplete — 577f1ca

### Phase 3: Prompts Module

#### Automated

- [x] 3.1 `npx tsc --noEmit` exits 0 — 088f6ab
- [x] 3.2 `npx tsx src/prompts/review.ts` exits 0 — 088f6ab

#### Manual

- [x] 3.3 Prompt strings match `main.py` exactly — 088f6ab

### Phase 4: Agent Module

#### Automated

- [x] 4.1 `npx tsc --noEmit` exits 0 — 275c4ad
- [x] 4.2 `npx tsx src/agent.ts` exits 0 — 275c4ad

#### Manual

- [x] 4.3 `codeReviewerAgent` importable without errors — 275c4ad
- [x] 4.4 `output` typed as `ReviewResult` in IDE — 275c4ad

### Phase 5: Main Entrypoint

#### Automated

- [x] 5.1 `npx tsc --noEmit` exits 0 — e149430
- [x] 5.2 `npm start` exits 0 with API key set — e149430

#### Manual

- [x] 5.3 Output prints summary, score, and issues for sample code — e149430
- [x] 5.4 No TypeScript errors in IDE across all new files — e149430