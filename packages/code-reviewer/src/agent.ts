import { InferAgentUIMessage, Output, ToolLoopAgent } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

import { reviewResultSchema } from './schemas/review';
import { SYSTEM_PROMPT } from './prompts/review';

const openrouter = createOpenRouter({ apiKey: process.env.OPENROUTER_API_KEY });

export const codeReviewerAgent = new ToolLoopAgent({
  model: openrouter('anthropic/claude-sonnet-4-6', { maxTokens: 2048 }),
  instructions: SYSTEM_PROMPT,
  output: Output.object({ schema: reviewResultSchema }),
});

export type CodeReviewerUIMessage = InferAgentUIMessage<typeof codeReviewerAgent>;