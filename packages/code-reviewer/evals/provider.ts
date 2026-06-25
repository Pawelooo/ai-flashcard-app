import { spawnSync } from 'child_process';
import * as path from 'path';
import { fileURLToPath } from 'url';

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const tsxCli = path.join(packageRoot, 'node_modules', 'tsx', 'dist', 'cli.mjs');

export default class CodeReviewerProvider {
  private model: string;

  constructor(config?: { model?: string }) {
    this.model = config?.model ?? 'anthropic/claude-sonnet-4-6';
  }

  id(): string {
    return `code-reviewer:${this.model}`;
  }

  async callApi(
    _prompt: string,
    context: { vars: Record<string, string> }
  ): Promise<{ output: string }> {
    const vars = context.vars;
    const diffPath = path.resolve(process.cwd(), vars.diff_file);

    const result = spawnSync(
      process.execPath,
      [tsxCli, '--env-file=../../.env', 'src/main.ts'],
      {
        cwd: packageRoot,
        env: {
          ...process.env,
          NODE_TLS_REJECT_UNAUTHORIZED: '0',
          OPENROUTER_MAX_TOKENS: '1500',
          DIFF_FILE: diffPath,
          PR_TITLE: vars.PR_TITLE,
          PR_DESCRIPTION: vars.PR_DESCRIPTION || '',
          OPENROUTER_MODEL: this.model,
        },
        encoding: 'utf-8',
        timeout: 120_000,
      }
    );

    if (result.status !== 0) {
      const tail = result.stderr.slice(-600);
      throw new Error(`Agent subprocess failed (exit ${result.status}):\n${tail}`);
    }

    return { output: result.stdout.trim() };
  }
}