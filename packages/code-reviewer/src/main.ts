// workaround for Windows corporate CA — mirrors native-tls = true in pyproject.toml
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

import { codeReviewerAgent } from './agent';
import { buildUserPrompt } from './prompts/review';

const sample = `
def add(a, b):
    return a + b

result = add(1, '2')
print(result)
`;

async function main(): Promise<void> {
  console.log('Reviewing sample code...');
  const { output } = await codeReviewerAgent.generate({ prompt: buildUserPrompt(sample) });
  console.log(`Summary : ${output.summary}`);
  console.log(`Score   : ${output.score}/10`);
  console.log('Issues  :');
  for (const issue of output.issues) {
    console.log(`  - ${issue}`);
  }
}

main().catch(console.error);