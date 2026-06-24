# CI/CD AI Code Review Workflow — Implementation Plan

## Overview

Add automated AI code review to every pull request targeting `master`. The review scores the diff on 6 criteria (1–10 each), posts a PR comment with results, and applies a pass/fail label. A retry mechanism is provided via the `ai-cr:review` label.

## Current State Analysis

- `packages/code-reviewer/` contains a working TypeScript reviewer using Vercel AI SDK v6 (`ai` ^6.0.207) and `ToolLoopAgent`.
- Agent currently calls `openai/gpt-4o-mini` via OpenRouter (`@openrouter/ai-sdk-provider`).
- Schema: `{summary, issues[], score(1–10)}` — single aggregate score, no per-criterion breakdown.
- System prompt is minimal; no rubrics for individual criteria.
- Entry point (`main.ts`) has a hardcoded sample diff and logs to the console — not usable from CI.
- No `.github/` directory exists; starting from scratch for all workflow files.

## Desired End State

On every PR to `master` (and on demand via label), GHA runs the AI reviewer and:
1. Posts a formatted PR comment with per-criterion scores, aggregate, summary, and issues.
2. Applies `ai-cr:passed` (aggregate ≥ 7) or `ai-cr:failed` (aggregate < 7).
3. Removes the `ai-cr:review` trigger label after completing a retry run.

Verify by opening a test PR and confirming the comment appears and the correct label is applied.

### Key Discoveries

- `ToolLoopAgent.generate({ prompt })` returns `{ output }` typed by the Zod schema — swapping the model only requires changing the provider import and model string in `agent.ts`. (`packages/code-reviewer/src/agent.ts:1–13`)
- `process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'` in `main.ts` is a Windows CA workaround — must be removed or platform-guarded before running on Linux GHA runners (security: bypasses TLS verification).
- `@ai-sdk/anthropic` is the correct Vercel AI SDK v6 provider for Anthropic; install alongside existing `ai` package.
- The `gh` CLI is pre-installed on `ubuntu-latest` runners — use it for PR comments and label management.
- Labels (`ai-cr:passed`, `ai-cr:failed`, `ai-cr:review`) do not exist yet; the composite action must create them idempotently with `gh label create --force`.

## What We're NOT Doing

- Not touching `src/main.py` — the Python implementation is a learning artifact and stays unchanged.
- Not bundling or compiling the TypeScript package; `tsx` runs it directly.
- Not publishing a reusable GitHub Action (no root-level `action.yml`).
- Not splitting large diffs across multiple API calls.
- Not enforcing a cost cap or token budget per review.
- Not auto-requesting re-review from human reviewers after AI review.

## Implementation Approach

Three-phase rollout: (1) extend the TS package so it's CI-consumable, (2) add a composite action that orchestrates the full review flow, (3) add the main workflow that triggers it. Each phase has independently verifiable success criteria.

## Critical Implementation Details

**TLS in GHA**: Remove `process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'` from `main.ts` unconditionally — GHA Linux runners have valid CA bundles, and leaving this on makes every HTTPS call insecure. The `pyproject.toml` `native-tls` flag is Python-only and unrelated.

**3-dot diff**: Use `git diff $BASE_SHA...$HEAD_SHA` (three dots = diff from merge-base to head, i.e., only what the PR branch changed). Two-dot diff includes master commits since branch point and inflates the diff with unrelated changes.

**Aggregate computed in TS, not by the model**: Remove `score` from the schema entirely; compute `aggregate_score = mean(Object.values(criteria))` in `main.ts` after the model returns per-criterion scores. This avoids asking the model to do arithmetic.

**Comment idempotency**: Search for an existing comment containing the HTML marker `<!-- ai-code-review -->` before posting. If found, PATCH it (avoiding comment spam on retries). Use the GitHub REST API via `gh api`.

---

## Phase 1: Extend packages/code-reviewer for CI

### Overview

Update the schema, prompts, agent, and entry point so the reviewer can be invoked from GHA with a real PR diff and outputs structured JSON to stdout.

### Changes Required

#### 1. Schema (`src/schemas/review.ts`)

**File**: `packages/code-reviewer/src/schemas/review.ts`

**Intent**: Replace the single `score` field with a `criteria` object holding 6 named integer scores. Remove `score` from the schema entirely — aggregate will be computed externally.

**Contract**: Export `reviewResultSchema` with shape `{ criteria: { implementation_correctness, idiomaticity, complexity, test_coverage, documentation, security_and_safety }, summary, issues }`. Each criterion field is `z.number().int().min(1).max(10)`. Export `ReviewResult` type as before.

#### 2. System prompt (`src/prompts/review.ts`)

**File**: `packages/code-reviewer/src/prompts/review.ts`

**Intent**: Replace the minimal system prompt with one that names all 6 criteria, includes the 1/10 anchor rubrics from `requirements.md`, and instructs the model to return scores only for those criteria. This aligns model output with the updated schema.

**Contract**: `SYSTEM_PROMPT` lists the 6 criteria with their rubrics verbatim (sourced from `requirements.md`). It instructs the model to return: one integer score per criterion, a `summary` string (2–4 sentences), and an `issues` array (one item per concrete problem found; empty if none).

The 6 criteria and their anchors to embed:
- `implementation_correctness` — 1: broken logic/regressions; 10: correct across happy path, edge cases, failures
- `idiomaticity` — 1: fights the stack; 10: indistinguishable from well-written surrounding code
- `complexity` — 1: over-engineered/tangled; 10: minimal and clear
- `test_coverage` — 1: risky logic ships untested; 10: risk-weighted coverage done well
- `documentation` — 1: opaque; 10: just enough "why" without restating the obvious
- `security_and_safety` — 1: exploitable flaw or leaked secret; 10: input validated, secrets safe, no new attack surface

#### 3. `buildUserPrompt` (`src/prompts/review.ts`)

**File**: `packages/code-reviewer/src/prompts/review.ts`

**Intent**: Update the prompt builder to include PR title (always), PR description (when present), and the diff. Giving the model the PR title helps it check whether the diff matches the stated intent.

**Contract**: `buildUserPrompt({ title: string, description?: string, diff: string }): string`. Output includes a `## PR Title` section, an optional `## PR Description` section (omitted when `description` is falsy), and a `## Diff` section.

#### 4. Agent (`src/agent.ts`)

**File**: `packages/code-reviewer/src/agent.ts`

**Intent**: Switch the model provider from OpenRouter to Anthropic and change the model to `claude-sonnet-4-6`. The `ToolLoopAgent` call signature stays identical; only the provider import and model value change.

**Contract**: Replace `createOpenRouter` + `@openrouter/ai-sdk-provider` with `createAnthropic` from `@ai-sdk/anthropic`. Model: `anthropic('claude-sonnet-4-6')`. API key env var: `OPENROUTER_API_KEY`.

#### 5. Entry point (`src/main.ts`)

**File**: `packages/code-reviewer/src/main.ts`

**Intent**: Replace the hardcoded sample diff with a CI-compatible entry point that reads PR context from env vars, runs the reviewer, computes the aggregate score, and emits JSON to stdout for the composite action to consume.

**Contract**:
- Remove the Windows TLS workaround line (`NODE_TLS_REJECT_UNAUTHORIZED`).
- Read `process.env.DIFF_FILE` (required) — path to a file containing the git diff.
- Read `process.env.PR_TITLE` (required) and `process.env.PR_DESCRIPTION` (optional, may be empty string).
- Pass `{ title, description, diff }` to `buildUserPrompt`.
- After `codeReviewerAgent.generate()`, compute `aggregate_score` as the arithmetic mean of the 6 criterion values, rounded to 1 decimal place.
- `console.log(JSON.stringify({ criteria: output.criteria, aggregate_score, summary: output.summary, issues: output.issues }))` — no other stdout.
- Exit non-zero (`process.exit(1)`) on any unhandled error.

#### 6. Package dependencies (`package.json`)

**File**: `packages/code-reviewer/package.json`

**Intent**: Add the Anthropic provider; remove the now-unused OpenRouter provider.

**Contract**: Add `@ai-sdk/anthropic` at a version compatible with `ai ^6.0.207` (check npm for the current compatible release). Remove `@openrouter/ai-sdk-provider`.

### Success Criteria

#### Automated Verification

- `cd packages/code-reviewer && npm install` exits 0 with no peer-dependency errors.
- Running `OPENROUTER_API_KEY=<real-key> DIFF_FILE=<path-to-any-.diff> PR_TITLE="test" npx tsx src/main.ts` exits 0 and prints valid JSON to stdout.
- The printed JSON contains keys: `criteria` (object with 6 integer scores), `aggregate_score` (number), `summary` (string), `issues` (array).

#### Manual Verification

- Per-criterion scores are plausible (not all 10, not all 1 for a real diff).
- `summary` is a coherent 2–4 sentence assessment.
- No extra output lines before or after the JSON.

**Implementation Note**: After completing Phase 1 and all automated verification passes, pause here for manual confirmation before proceeding to Phase 2.

---

## Phase 2: Composite Action

### Overview

Encapsulate the full review flow — diff extraction, model call, comment, labels — in a composite action so the main workflow YAML stays minimal and the action can be tested independently.

### Changes Required

#### 1. Composite action definition

**File**: `.github/actions/ai-code-review/action.yml`

**Intent**: Accept the minimal inputs needed to run the review, then orchestrate: get the diff, optionally get the PR description, run the TS reviewer, post/update the PR comment, manage labels.

**Contract**: Composite action with the following inputs:

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic-api-key` | yes | — | `OPENROUTER_API_KEY` for the model call |
| `github-token` | yes | — | For PR comment and label API calls |
| `pr-number` | yes | — | PR number (integer as string) |
| `pr-title` | yes | — | PR title string |
| `base-sha` | yes | — | Merge-base SHA for diff |
| `head-sha` | yes | — | Head SHA for diff |
| `include-description` | no | `'false'` | When `'true'`, fetch and include PR body |

Steps (all `shell: bash`):

1. **Setup Node 20** — `uses: actions/setup-node@v4` with `node-version: '20'`.

2. **Install dependencies** — `cd packages/code-reviewer && npm ci` (or `npm install` if no lock file is committed).

3. **Create labels (idempotent)** — run `gh label create ai-cr:passed --color 0e8a16 --force`, `gh label create ai-cr:failed --color d93f0b --force`, `gh label create ai-cr:review --color 0075ca --force`. Requires `GITHUB_TOKEN` env var.

4. **Get diff** — `git diff ${{ inputs.base-sha }}...${{ inputs.head-sha }} > /tmp/pr.diff`. If the diff is empty, skip the model call and post a comment noting "no changes to review".

5. **Get PR description (conditional)** — `if [ "${{ inputs.include-description }}" = "true" ]; then gh pr view ${{ inputs.pr-number }} --json body --jq .body > /tmp/pr.description; fi`.

6. **Run reviewer** — invoke `npx tsx src/main.ts` from `packages/code-reviewer/` with env vars: `OPENROUTER_API_KEY`, `DIFF_FILE=/tmp/pr.diff`, `PR_TITLE`, `PR_DESCRIPTION` (read from `/tmp/pr.description` or empty string). Capture stdout as `REVIEW_JSON`.

7. **Build comment body** — construct a markdown string with the HTML marker `<!-- ai-code-review -->`, a score table (6 rows), the aggregate, summary, issues list, and pass/fail verdict. Assign to a step output or `COMMENT_BODY` env var.

8. **Post or update comment** — search existing comments on the PR for `<!-- ai-code-review -->` via `gh api repos/{owner}/{repo}/issues/{number}/comments`. If found, PATCH the existing comment body. If not found, create a new comment with `gh pr comment`.

9. **Manage labels** — remove `ai-cr:passed` and `ai-cr:failed` if present (best-effort, ignore 404s), then add the appropriate label based on whether `aggregate_score >= 7`.

10. **Remove trigger label** — `gh pr edit ${{ inputs.pr-number }} --remove-label ai-cr:review` (best-effort, ignore errors — label may not be present on first-run triggers).

### Success Criteria

#### Automated Verification

- `yamllint .github/actions/ai-code-review/action.yml` exits 0 (or GitHub schema validation in a test run).
- All `gh` commands reference the correct env var for auth (`GITHUB_TOKEN`).

#### Manual Verification

- Trigger the action on a test PR: the PR comment appears with the full score table.
- On a second trigger (label retry): the existing comment is updated, not duplicated.
- Labels `ai-cr:passed` / `ai-cr:failed` are mutually exclusive on the PR after each run.
- `ai-cr:review` label is removed after a retry run completes.

**Implementation Note**: After completing Phase 2 and all automated verification passes, pause here for manual confirmation before proceeding to Phase 3.

---

## Phase 3: Main Workflow

### Overview

Wire the composite action into a GHA workflow triggered by PR events and the label retry mechanism.

### Changes Required

#### 1. Workflow definition

**File**: `.github/workflows/code-review.yml`

**Intent**: Trigger the composite action on every relevant PR event and on the label retry signal, with the minimum permissions required.

**Contract**:

Triggers:
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, labeled]
    branches: [master]
```

Job condition (filters label events to only the retry label):
```yaml
if: github.event.action != 'labeled' || github.event.label.name == 'ai-cr:review'
```

Permissions (minimum required):
```yaml
permissions:
  contents: read
  pull-requests: write
```

Steps:
1. `actions/checkout@v4` with `fetch-depth: 0` (required for `git diff` across SHAs).
2. Call `./.github/actions/ai-code-review` passing:
   - `anthropic-api-key: ${{ secrets.OPENROUTER_API_KEY }}`
   - `github-token: ${{ secrets.GITHUB_TOKEN }}`
   - `pr-number: ${{ github.event.pull_request.number }}`
   - `pr-title: ${{ github.event.pull_request.title }}`
   - `base-sha: ${{ github.event.pull_request.base.sha }}`
   - `head-sha: ${{ github.event.pull_request.head.sha }}`
   - `include-description: 'false'` (hardcoded default; can be changed later)

### Success Criteria

#### Automated Verification

- `yamllint .github/workflows/code-review.yml` exits 0.
- The workflow file references the secret `OPENROUTER_API_KEY` — confirm this secret exists in the repo settings before the first run.

#### Manual Verification

- Open a test PR to `master`: workflow run appears in Actions tab within ~30s.
- Run completes without errors; PR comment and label are visible.
- Add `ai-cr:review` label to an existing PR: a second workflow run triggers and updates the comment.
- No workflow run triggers for non-label events other than opened/synchronize/reopened.

---

## Testing Strategy

### Manual Testing Steps

1. Create `OPENROUTER_API_KEY` secret in GitHub repo settings.
2. Open a PR with a small Python or TypeScript change.
3. Confirm: Actions tab shows a `code-review` run; PR comment appears; `ai-cr:passed` or `ai-cr:failed` label is applied.
4. Push another commit to the same PR (synchronize event): comment is updated (not duplicated), label is refreshed.
5. Add `ai-cr:review` label: retry run triggers, existing comment is updated, label is removed.
6. Test with `include-description: 'true'` by temporarily editing the workflow input: confirm the review mentions PR intent alignment.

## Migration Notes

- The `OPENROUTER_API_KEY` secret (if set in CI) can be removed once the workflow is live.
- `src/main.py` is unaffected; it still uses OpenAI/OpenRouter for local dev experiments.

## References

- Requirements: `context/changes/ci-cd/requirements.md`
- Vercel AI SDK `ToolLoopAgent`: `packages/code-reviewer/src/agent.ts`
- Schema to extend: `packages/code-reviewer/src/schemas/review.ts:1–8`
- Prompts to rewrite: `packages/code-reviewer/src/prompts/review.ts:1–6`

---

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Extend packages/code-reviewer for CI

#### Automated

- [x] 1.1 `npm install` exits 0 with no peer-dependency errors after package.json update
- [x] 1.2 `OPENROUTER_API_KEY=<key> DIFF_FILE=<path> PR_TITLE="test" npx tsx src/main.ts` exits 0 and prints valid JSON
- [x] 1.3 Printed JSON contains `criteria` (6 scores), `aggregate_score`, `summary`, `issues`

#### Manual

- [x] 1.4 Per-criterion scores are plausible for a real diff
- [x] 1.5 `summary` is coherent; no extra stdout lines around the JSON

### Phase 2: Composite Action

#### Automated

- [ ] 2.1 `action.yml` passes YAML validation
- [ ] 2.2 All `gh` commands use `GITHUB_TOKEN` env var correctly

#### Manual

- [ ] 2.3 Test PR shows full score table in PR comment
- [ ] 2.4 Retry (label trigger) updates the comment, does not duplicate it
- [ ] 2.5 Pass/fail labels are mutually exclusive after each run
- [ ] 2.6 `ai-cr:review` label is removed after retry completes

### Phase 3: Main Workflow

#### Automated

- [ ] 3.1 `code-review.yml` passes YAML validation
- [ ] 3.2 `OPENROUTER_API_KEY` secret exists in repo settings

#### Manual

- [ ] 3.3 Workflow run appears in Actions tab on PR open
- [ ] 3.4 Synchronize event updates comment without duplication
- [ ] 3.5 Label retry triggers a second run correctly
- [ ] 3.6 Non-target label events do not trigger a workflow run
