# CI/CD AI Code Review Workflow — Plan Brief

> Full plan: `context/changes/ci-cd/plan.md`
> Requirements: `context/changes/ci-cd/requirements.md`

## What & Why

Add automated AI code review to every PR targeting `master`. The reviewer scores the diff on 6 criteria (implementation correctness, idiomaticity, complexity, test coverage, documentation, security), posts a formatted comment, and gates with a pass/fail label — giving contributors structured, consistent feedback without manual review latency.

## Starting Point

`packages/code-reviewer/` already has a working `ToolLoopAgent`-based TypeScript reviewer using Vercel AI SDK v6 and OpenRouter/gpt-4o-mini. Its schema returns a single aggregate score; the entry point has a hardcoded sample diff and logs to stdout. No `.github/` directory exists.

## Desired End State

Every new PR to `master` automatically gets an AI review comment with a 6-criterion score table and an aggregate, and is labelled `ai-cr:passed` (≥ 7/10) or `ai-cr:failed` (< 7/10). A reviewer can re-trigger the check by adding the `ai-cr:review` label, which is removed after the retry completes.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|----------|--------|------------------|--------|
| PR description in review | Exclude by default (`include-description: 'false'`) | Avoids token cost for most PRs while leaving opt-in available | Plan |
| Score schema | 6 per-criterion scores + computed aggregate | Actionable — shows exactly which criterion dragged the score down | Plan |
| Pass/fail threshold | Aggregate ≥ 7 = passed | Common "good but not perfect" bar, easy to explain to contributors | Plan |
| Model | `claude-sonnet-4-6` via `@ai-sdk/anthropic` | Frontier reasoning quality; consistent with project's Claude usage | Plan |
| Build strategy | Run directly with `tsx` (no bundle) | No build step; matches the existing dev workflow exactly | Plan |
| Retry label cleanup | Remove `ai-cr:review` after each run | Clean state — label can be re-added to trigger another retry | Plan |
| Aggregate computation | Computed in TS (`mean` of 6 scores), not by model | Avoids asking the model to do arithmetic; more reliable | Plan |
| Comment strategy | Find-and-update existing comment (HTML marker) | Avoids comment spam on retries | Plan |

## Scope

**In scope:**
- Schema extension: 6 per-criterion scores, remove single `score` field
- System prompt rewrite with rubrics from `requirements.md`
- Agent switch: OpenRouter/gpt-4o-mini → Anthropic/claude-sonnet-4-6
- CI-ready entry point: reads diff from file, emits JSON to stdout
- Composite action: diff extraction, model call, comment, labels
- Main workflow: PR triggers + label retry

**Out of scope:**
- Python reviewer (`main.py`) — unchanged
- Bundling/compiling the TS package
- Publishing as a standalone/reusable GitHub Action
- Per-file diff splitting or token budgeting
- Business alignment / architectural fit criteria (parked in requirements)

## Architecture / Approach

The composite action (`.github/actions/ai-code-review/`) is the single orchestrator: it gets the 3-dot diff via `git diff`, optionally fetches the PR body via `gh`, runs `tsx packages/code-reviewer/src/main.ts` with env vars, parses the JSON stdout, and makes two GitHub API calls (comment upsert, label swap). The main workflow (`code-review.yml`) is a thin trigger layer — checkout + call action + pass secrets.

```
pull_request event
       │
       ▼
code-review.yml (main workflow)
  └─ .github/actions/ai-code-review (composite)
       ├─ git diff base...head > /tmp/pr.diff
       ├─ tsx packages/code-reviewer/src/main.ts  →  JSON to stdout
       ├─ gh api  →  upsert PR comment
       └─ gh pr edit  →  swap ai-cr:passed / ai-cr:failed label
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|-------|-----------------|----------|
| 1. Extend code-reviewer | Schema + prompt + agent + CI entry point | `@ai-sdk/anthropic` version compatibility with `ai ^6.0.207` |
| 2. Composite action | Full review flow (diff → model → comment → labels) | Comment upsert logic (search-then-patch via REST API) |
| 3. Main workflow | GHA trigger wiring for PR events + label retry | `OPENROUTER_API_KEY` secret must be set before first run |

**Prerequisites:** `OPENROUTER_API_KEY` secret added to GitHub repo settings before Phase 3 can be tested.  
**Estimated effort:** ~2–3 sessions across 3 phases.

## Open Risks & Assumptions

- `@ai-sdk/anthropic` version compatible with `ai ^6` needs to be confirmed at install time — peer-dep mismatch would break Phase 1.
- Very large diffs (> 100 KB) may hit model context limits — not handled in this plan; treat as a future improvement.
- `gh` CLI is assumed pre-installed on `ubuntu-latest` — this is true as of 2025 but worth verifying in the first run.
- The `ToolLoopAgent` import from `'ai'` v6 is confirmed present; if the Vercel AI SDK drops it in a future patch, agent.ts will need updating.

## Success Criteria (Summary)

- A test PR to `master` receives an AI review comment with 6 criterion scores and a pass/fail label within ~2 minutes of opening.
- Adding the `ai-cr:review` label re-triggers the review and updates (not duplicates) the comment.
- `main.ts` emits valid JSON on any real diff when invoked with the correct env vars.
