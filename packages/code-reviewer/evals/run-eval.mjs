import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.join(__dirname, '..');
const promptfooEntry = path.join(packageRoot, 'node_modules', 'promptfoo', 'dist', 'src', 'entrypoint.js');

const result = spawnSync(
  process.execPath,
  [promptfooEntry, 'eval', '--env-file=../../.env', ...process.argv.slice(2)],
  {
    stdio: 'inherit',
    cwd: packageRoot,
    env: { ...process.env, NODE_TLS_REJECT_UNAUTHORIZED: '0' },
  }
);
process.exit(result.status ?? 0);