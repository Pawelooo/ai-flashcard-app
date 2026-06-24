import { readFileSync } from 'fs';
import { codeReviewerAgent } from './agent';
import { buildUserPrompt } from './prompts/review';

async function main(): Promise<void> {
  const diffFile = process.env.DIFF_FILE;
  const prTitle = process.env.PR_TITLE;

  if (!diffFile) throw new Error('DIFF_FILE env var is required');
  if (!prTitle) throw new Error('PR_TITLE env var is required');

  const diff = readFileSync(diffFile, 'utf-8');
  const description = process.env.PR_DESCRIPTION || undefined;

  const { output } = await codeReviewerAgent.generate({
    prompt: buildUserPrompt({ title: prTitle, description, diff }),
  });

  const scores = Object.values(output.criteria).map((c) => c.score);
  const aggregate_score = Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;

  console.log(JSON.stringify({
    criteria: output.criteria,
    aggregate_score,
    summary: output.summary,
    issues: output.issues,
  }));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
