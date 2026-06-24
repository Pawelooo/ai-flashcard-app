import { z } from 'zod';

const criterionSchema = z.object({
  score: z.number(),
  rationale: z.string(),
});

const criteriaSchema = z.object({
  implementation_correctness: criterionSchema,
  idiomaticity: criterionSchema,
  complexity: criterionSchema,
  test_coverage: criterionSchema,
  documentation: criterionSchema,
  security_and_safety: criterionSchema,
});

export const reviewResultSchema = z.object({
  criteria: criteriaSchema,
  summary: z.string(),
  issues: z.array(z.string()),
});

export type ReviewResult = z.infer<typeof reviewResultSchema>;