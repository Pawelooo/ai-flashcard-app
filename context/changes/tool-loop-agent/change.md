---
id: tool-loop-agent
title: Convert code-reviewer to AI SDK ToolLoopAgent
status: implementing
created: 2026-06-21
updated: 2026-06-21
---

Migrate `packages/code-reviewer/src/main.py` (Python + OpenAI SDK) to a modular TypeScript module using the Vercel AI SDK `ToolLoopAgent`. Extract schemas and prompts into dedicated modules. Export a reusable agent instance suitable for future promptfoo evals.
