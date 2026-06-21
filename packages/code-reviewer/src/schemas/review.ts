import { z } from 'zod';

export const reviewResultSchema = z.object({
  summary: z.string(),
  issues: z.array(z.string()),
  score: z.number().int().min(1).max(10),
});

export type ReviewResult = z.infer<typeof reviewResultSchema>;