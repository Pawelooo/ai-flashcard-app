
# Promptfoo Evaluation Suite for Code Reviewer — Implementation Plan

## Overview

Introduce [promptfoo](https://promptfoo.dev) to `packages/code-reviewer` to run the existing AI code review prompt against three OpenRouter models side by side (claude-sonnet-4-6 as baseline, z-ai/glm-5.1, deepseek/deepseek-v4-flash). A single Django diff fixture with three deliberate flaws serves as the test case; two assertions — a static JavaScript check and an LLM-as-a-judge rubric — verify whether each model correctly identifies those flaws.

## Current State Analysis

- `packages/code-reviewer/src/agent.ts` exports a singleton `codeReviewerAgent` instantiated at module load with `OPENROUTER_MODEL` env var. Per-process, the model is fixed — unsuitable for promptfoo's in-process multi-model evaluation.
- `src/prompts/review.ts` exports `SYSTEM_PROMPT` and `buildUserPrompt({ title, description?, diff })` — fully reusable by the eval provider.
- `src/schemas/review.ts` exports `reviewResultSchema` (Zod, 6 criteria with `score`+`rationale`) and the `ReviewResult` type.
- No `promptfoo` dependency, no `evals/` directory, and no `.diff` fixtures exist.
- `package.json` `"type": "commonjs"`, tsx@4 for runtime, ai@^6.0.207.

## Desired End State

Running `npm run eval` from `packages/code-reviewer/` triggers `promptfoo eval` and produces a side-by-side HTML/CLI report showing all three models scored against the Django fixture. For a model to pass, it must score `aggregate_score ≤ 6` on the flawed diff **and** the LLM-as-a-judge must confirm all three flaws were identified. The suite runs without network mocking — it hits the real OpenRouter API.

### Key Discoveries

- `src/agent.ts:9` — model is read from `process.env.OPENROUTER_MODEL` at module load. Adding an exported factory `createCodeReviewerAgent(model, opts?)` is the minimal change needed to support per-call model selection without touching the CI singleton.
- `package.json:7` — `"start": "tsx --env-file=../../.env src/main.ts"`. Running promptfoo from `packages/code-reviewer/` with the same `.env` file passes `OPENROUTER_API_KEY` automatically.
- `tsconfig.json` uses `moduleResolution: "Bundler"`. Promptfoo compiles TypeScript providers with its own esbuild bundler, which supports bundler-style resolution — no separate tsconfig needed.
- `maxTokens: 2048` in `agent.ts:12` is borderline for a complex diff. The factory must accept an optional override so evals can use a higher budget without altering the CI path.

## What We're NOT Doing

- Not modifying `src/main.ts` — the CI entry point is unchanged.
- Not changing the default `codeReviewerAgent` singleton — CI backward-compatibility is preserved.
- Not creating a Docker or isolated test environment — the eval hits the real API.
- Not adding golden-file snapshot tests (output is non-deterministic).
- Not publishing the eval suite as a separate package or npm workspace.
- Not adding a second fixture yet — one complex fixture is sufficient for the first eval run.

## Implementation Approach

Minimal surface area: add promptfoo as a dev dependency, extend `agent.ts` with a factory (two new lines), write a thin custom TypeScript provider that reuses existing exports, author the Django diff fixture, and declare the promptfoo config. The custom provider pattern (vs. `exec` subprocess) avoids shell env-var gymnastics and keeps the evaluation in-process with typed imports.

## Critical Implementation Details

**Factory must not break the singleton.** The existing `const codeReviewerAgent = createCodeReviewerAgent(...)` export in `agent.ts` is used by `main.ts` in CI. Any change to `agent.ts` must preserve that export with identical behavior.

**maxTokens for evals.** The Django fixture response (6 criteria × rationale + summary + issues) can approach 1 500 tokens of output. Set `maxTokens: 4096` in the eval provider call to avoid truncation; the CI path keeps its existing 2 048.

**promptfoo provider path resolution.** `file://evals/provider.ts` in `promptfooconfig.yaml` is resolved relative to the config file location (`packages/code-reviewer/`). All `readFileSync` calls inside `provider.ts` for the diff file must use `path.resolve(process.cwd(), vars.diff_file)` to stay portable.

**LLM-as-a-judge provider string.** Promptfoo's built-in OpenRouter support uses `openrouter:<model-id>` as the provider identifier and reads `OPENROUTER_API_KEY` from env. No extra configuration needed beyond what the .env already supplies.

---

## Phase 1: Install promptfoo and scaffold eval structure

### Overview

Add promptfoo as a dev dependency and create the `evals/` directory layout. No functional code changes — just tooling and skeleton files.

### Changes Required

#### 1. Package dependency

**File**: `packages/code-reviewer/package.json`

**Intent**: Add `promptfoo` as a dev dependency and an `eval` npm script.

**Contract**:
- Add `"promptfoo": "latest"` under `devDependencies`.
- Add `"eval": "promptfoo eval"` under `scripts`.
- Pin to `"latest"` initially; lock down a specific version once `npm install` resolves it (record the resolved version in the plan progress note).

#### 2. Eval directory structure

**File**: `packages/code-reviewer/evals/` (new directory)

**Intent**: Create the `evals/` directory with a `fixtures/` subdirectory. Both are empty placeholders at this phase.

**Contract**: After this phase, `packages/code-reviewer/evals/fixtures/` exists. A `.gitkeep` is not needed — Phase 2 adds the first real file.

### Success Criteria

#### Automated Verification

- `cd packages/code-reviewer && npm install` exits 0, `promptfoo` binary resolves: `npx promptfoo --version` prints a version string.
- `evals/fixtures/` directory exists.

#### Manual Verification

- No peer-dependency warnings about `promptfoo` being incompatible with the existing `ai@^6.0.207` or `zod@^4` versions.

**Implementation Note**: After completing Phase 1 and automated verification passes, confirm manually before proceeding to Phase 2.

---

## Phase 2: Author Django diff fixture

### Overview

Write a realistic unified diff that adds a `UserCardStatsView` to the existing `flashcards` app. The diff contains exactly three deliberate flaws, each targeting a distinct review criterion.

### Changes Required

#### 1. Diff fixture file

**File**: `packages/code-reviewer/evals/fixtures/django-card-stats.diff`

**Intent**: Provide a self-contained unified diff that looks like a real PR in this project. The diff touches `flashcards/views.py` and `flashcards/urls.py`. Three flaws are embedded deliberately.

**Contract**: The three flaws and their target criteria:

| # | Flaw | Target criterion | Expected signal |
|---|---|---|---|
| 1 | `UserCardStatsView(TemplateView)` has no `LoginRequiredMixin` and no `@login_required` — an unauthenticated user can access `/flashcards/my-stats/` | `security_and_safety` | score ≤ 4, rationale mentions authentication |
| 2 | `CardReview.objects.filter(user=user).latest('reviewed_at')` raises `CardReview.DoesNotExist` for users with no reviews — no `try/except` or `.first()` guard | `implementation_correctness` | score ≤ 4, rationale mentions unhandled exception |
| 3 | `CardReview.objects.filter(user=user).count() > 0` to check existence — Django idiom is `.exists()` | `idiomaticity` | score ≤ 5, rationale mentions `.exists()` |

The diff must be syntactically valid unified diff format (`diff --git a/...`) and the added code must be plausible Django. Outside of the three flaws, the added code should be idiomatic (correct indentation, correct imports, sensible variable names) so that the flaws stand out rather than being buried in noise.

Sketch of the diff:
```diff
diff --git a/flashcards/views.py b/flashcards/views.py
--- a/flashcards/views.py
+++ b/flashcards/views.py
@@ -1,6 +1,7 @@
-from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
+from django.views.generic import (
+    ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView,
+)
 from django.contrib.auth.mixins import LoginRequiredMixin
 ...

+
+class UserCardStatsView(TemplateView):          # ← Flaw 1: no LoginRequiredMixin
+    template_name = "flashcards/user_stats.html"
+
+    def get_context_data(self, **kwargs):
+        context = super().get_context_data(**kwargs)
+        user = self.request.user
+        context["total_reviews"] = CardReview.objects.filter(user=user).count()
+        context["has_reviews"] = (                # ← Flaw 3: use .exists()
+            CardReview.objects.filter(user=user).count() > 0
+        )
+        context["latest_review"] = (              # ← Flaw 2: no DoesNotExist guard
+            CardReview.objects.filter(user=user).latest("reviewed_at")
+        )
+        context["correct_count"] = CardReview.objects.filter(
+            user=user, is_correct=True
+        ).count()
+        return context

diff --git a/flashcards/urls.py b/flashcards/urls.py
--- a/flashcards/urls.py
+++ b/flashcards/urls.py
@@ ... @@
+    path("my-stats/", UserCardStatsView.as_view(), name="user_stats"),
```

Write the actual file with real line numbers and correct hunk headers (do not leave `@@ ... @@` as placeholder — compute real offsets based on the existing views.py).

### Success Criteria

#### Automated Verification

- `git apply --check packages/code-reviewer/evals/fixtures/django-card-stats.diff` exits 0 from the repo root (patch applies cleanly to the current tree).

#### Manual Verification

- Reading the diff, the three flaws are identifiable without external context.
- The surrounding code looks realistic and idiomatic (no obvious noise that would confuse the reviewer model).

**Implementation Note**: After Phase 2 automated verification passes, confirm the diff applies cleanly before proceeding.

---

## Phase 3: Extend agent factory and write eval provider

### Overview

Add a `createCodeReviewerAgent(model, opts?)` factory to `src/agent.ts` (backward-compatible), then write `evals/provider.ts` as a promptfoo custom TypeScript provider that creates a fresh agent per invocation.

### Changes Required

#### 1. Agent factory (`src/agent.ts`)

**File**: `packages/code-reviewer/src/agent.ts`

**Intent**: Export a factory function so the eval provider (and future callers) can instantiate the agent with an arbitrary model string and token budget, without touching the existing CI singleton.

**Contract**: Add `export function createCodeReviewerAgent(model: string, opts?: { maxTokens?: number })` above the existing `codeReviewerAgent` constant. The singleton becomes:
```typescript
export const codeReviewerAgent = createCodeReviewerAgent(
  process.env.OPENROUTER_MODEL ?? 'anthropic/claude-sonnet-4-6'
);
```
The factory body is identical to the current inline object literal, but uses `model` and `opts?.maxTokens ?? 2048` instead of the captured constants.

#### 2. Eval provider (`evals/provider.ts`)

**File**: `packages/code-reviewer/evals/provider.ts`

**Intent**: Implement a promptfoo custom TypeScript provider that:
1. Reads `PR_TITLE`, `PR_DESCRIPTION` (optional), and `diff_file` (path) from `context.vars`.
2. Reads the diff content from disk using `path.resolve(process.cwd(), vars.diff_file)`.
3. Creates a fresh agent via `createCodeReviewerAgent(model, { maxTokens: 4096 })` using the model string from `context.provider.config.model`.
4. Calls `buildUserPrompt` with the vars, runs `agent.generate()`, computes `aggregate_score`, and returns `{ output: JSON.stringify({...}) }`.

**Contract**: Export a default object with `id` and `callApi` matching the promptfoo provider interface:
```typescript
export default {
  id(): string { return 'code-reviewer'; },
  async callApi(
    _prompt: string,
    context: { vars: Record<string, string>; provider: { config?: { model?: string } } }
  ): Promise<{ output: string }> { ... }
};
```
The `_prompt` parameter (promptfoo's rendered template) is intentionally ignored — the provider builds the prompt internally via `buildUserPrompt`.

### Success Criteria

#### Automated Verification

- `npx tsc --noEmit` from `packages/code-reviewer/` exits 0 after both file changes.
- Importing the provider file via Node does not throw at module load: `node -e "require('./evals/provider.ts')"` (via tsx) exits without error.

#### Manual Verification

- `src/main.ts` still runs correctly (`npm start` with a real diff): the singleton agent is unaffected.

**Implementation Note**: After Phase 3 automated verification passes and manual check confirms CI path is intact, proceed.

---

## Phase 4: Write promptfooconfig.yaml and verify end-to-end

### Overview

Declare the three providers, the single test case with the Django fixture, and two assertions. Then run `npm run eval` and confirm the report is produced.

### Changes Required

#### 1. Promptfoo configuration

**File**: `packages/code-reviewer/promptfooconfig.yaml`

**Intent**: Define the evaluation: three model variants of the same custom provider, one test case pointing at the fixture, two assertions.

**Contract**: The file must declare:

```yaml
description: "Code review prompt — 3 models on a Django diff with 3 known flaws"

providers:
  - id: file://evals/provider.ts
    label: claude-sonnet-4-6
    config:
      model: anthropic/claude-sonnet-4-6
  - id: file://evals/provider.ts
    label: glm-5-1
    config:
      model: z-ai/glm-5.1
  - id: file://evals/provider.ts
    label: deepseek-v4-flash
    config:
      model: deepseek/deepseek-v4-flash

prompts:
  - "{{PR_TITLE}}"

tests:
  - description: "UserCardStatsView — 3 known flaws: auth missing, DoesNotExist unhandled, count()>0 vs exists()"
    vars:
      PR_TITLE: "Add user card statistics view"
      PR_DESCRIPTION: ""
      diff_file: "evals/fixtures/django-card-stats.diff"
    assert:
      - type: javascript
        value: "JSON.parse(output).aggregate_score <= 6"
        description: "Reviewer must score this flawed diff at or below 6"
      - type: llm-rubric
        value: |
          The code review output must identify all three of the following issues:
          1. The view is not protected by authentication (missing LoginRequiredMixin or @login_required).
          2. The query .latest('reviewed_at') will raise DoesNotExist when the user has no reviews.
          3. Using .count() > 0 is non-idiomatic Django; .exists() should be used instead.
        provider: openrouter:anthropic/claude-sonnet-4-6
```

The `prompts` section is required by promptfoo even though `evals/provider.ts` ignores the rendered prompt. A single `"{{PR_TITLE}}"` placeholder satisfies the parser while passing no content the provider needs.

### Success Criteria

#### Automated Verification

- `cd packages/code-reviewer && npm run eval` exits 0.
- CLI output shows a results table with 3 model columns and 1 test row.
- At least one model row shows `aggregate_score ≤ 6` in the assertion column.

#### Manual Verification

- Open the HTML report (`promptfoo view` or the URL printed to stdout): all three model outputs are visible.
- The LLM-as-a-judge pass/fail is recorded per model (not all three need to pass — the report shows which models identified which flaws).
- Claude Sonnet baseline is visibly better at identifying flaws than at least one of the cheaper models, OR all three pass (both outcomes are valid; the eval is for comparison, not a hard gate).

**Implementation Note**: If `npm run eval` exits non-zero due to an API error (rate limit, wrong model ID), retry once and note the error in the progress log. Do not mark Phase 4 automated verification complete until the full table renders.

---

## Testing Strategy

### Automated Tests

- `npx tsc --noEmit` — verifies TypeScript after `agent.ts` change and `provider.ts` creation.
- `git apply --check` — verifies the fixture diff applies cleanly.
- `npm run eval` — the eval itself is the integration test.

### Manual Testing Steps

1. Confirm `npm run eval` produces the results table in the CLI.
2. Open the HTML report and verify per-criterion scores and rationale text are visible per model.
3. Check that `aggregate_score` values look plausible (not all the same, not all 10).
4. Verify `src/main.ts` still works as CI entry point: `DIFF_FILE=evals/fixtures/django-card-stats.diff PR_TITLE="test" npm start` emits valid JSON.

## Migration Notes

- The `codeReviewerAgent` singleton in `agent.ts` is unchanged in behavior — no CI migration needed.
- `promptfoo` is a dev dependency only; it is not installed in production or on GHA runners running the existing `code-review.yml` workflow.
- The `evals/` directory and `promptfooconfig.yaml` can be ignored by `.gitignore` if the fixture diff contains sensitive data — but it does not in this case, so commit everything.

## References

- Research: `context/changes/code-review-evals/research.md`
- Requirements (review criteria rubrics): `context/changes/ci-cd/requirements.md`
- Agent singleton: `packages/code-reviewer/src/agent.ts:1–15`
- Prompts: `packages/code-reviewer/src/prompts/review.ts:1–52`
- Schema: `packages/code-reviewer/src/schemas/review.ts:1–23`
- Existing views (basis for fixture): `flashcards/views.py`
- Existing urls (basis for fixture): `flashcards/urls.py`

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Install promptfoo and scaffold eval structure

#### Automated

- [x] 1.1 `npm install` exits 0 after adding promptfoo devDependency — d086fc1
- [x] 1.2 `npx promptfoo --version` prints a version string — d086fc1
- [x] 1.3 `evals/fixtures/` directory exists — d086fc1

#### Manual

- [x] 1.4 No peer-dependency warnings incompatible with ai@^6 or zod@^4 — d086fc1

### Phase 2: Author Django diff fixture

#### Automated

- [x] 2.1 `git apply --check packages/code-reviewer/evals/fixtures/django-card-stats.diff` exits 0 — 2ccf409

#### Manual

- [x] 2.2 Three flaws are identifiable on a plain reading of the diff — 2ccf409
- [x] 2.3 Surrounding code looks idiomatic Django — 2ccf409

### Phase 3: Extend agent factory and write eval provider

#### Automated

- [x] 3.1 `npx tsc --noEmit` exits 0 after agent.ts and provider.ts changes — bcc8a99
- [x] 3.2 Provider file loads without error (no import-time crash) — bcc8a99

#### Manual

- [x] 3.3 `npm start` with a real diff still emits valid JSON (CI path unaffected) — bcc8a99

### Phase 4: Write promptfooconfig.yaml and verify end-to-end

#### Automated

- [x] 4.1 `npm run eval` exits 0 — bee9801
- [x] 4.2 CLI shows results table with 3 model columns and 1 test row — bee9801
- [x] 4.3 At least one model shows `aggregate_score ≤ 6` — bee9801

#### Manual

- [x] 4.4 HTML report shows per-criterion scores and rationales for all three models — bee9801
- [x] 4.5 LLM-as-a-judge pass/fail is recorded per model — bee9801
- [x] 4.6 `npm start` with the fixture diff still emits valid JSON after all changes — bee9801
