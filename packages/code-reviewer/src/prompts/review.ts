export const SYSTEM_PROMPT =
  'You are a code reviewer. Analyse the provided code and return structured feedback.';

export function buildUserPrompt(code: string): string {
  return `Review this code:\n\n${code}`;
}