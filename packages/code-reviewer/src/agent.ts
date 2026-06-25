import { InferAgentUIMessage, Output, ToolLoopAgent } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

import { reviewResultSchema } from './schemas/review';
import { SYSTEM_PROMPT } from './prompts/review';

const openrouter = createOpenRouter({ apiKey: process.env.OPENROUTER_API_KEY });

export function createCodeReviewerAgent(model: string, opts?: { maxTokens?: number }) {
  return new ToolLoopAgent({
    model: openrouter(model, { maxTokens: opts?.maxTokens ?? 2048 }),
    instructions: SYSTEM_PROMPT,
    output: Output.object({ schema: reviewResultSchema }),
  });
}

const model = process.env.OPENROUTER_MODEL ?? 'anthropic/claude-sonnet-4-6';
const maxTokens = Number(process.env.OPENROUTER_MAX_TOKENS ?? '2048');

export const codeReviewerAgent = createCodeReviewerAgent(model, { maxTokens });

export type CodeReviewerUIMessage = InferAgentUIMessage<typeof codeReviewerAgent>;