# AI Rules (Gemini Code Assist)

## Goals
- Prefer minimal diffs; do not refactor unrelated code.
- Keep public interfaces stable unless explicitly requested.
- Avoid new dependencies unless requested.

## Python / Flask
- Python 3.x. Use existing patterns in the repo.
- Validate request inputs; return consistent JSON errors.
- Use structured JSON logging; never log secrets.
- Add/adjust unit tests for logic changes.
- Update documentation when features or APIs are modified.

## Node
- Keep handlers/services pure where possible.
- Preserve API contracts and error shapes.
- Add tests for edge cases.

## React / Next.js
- Follow existing component patterns and folder structure.
- Prefer small, composable components.
- Don’t change design system primitives unless asked.
- Keep layout/styling consistent with existing approach.

## Output format (when asked)
- Prefer unified diff.
- Include commands to run relevant tests/lints if needed.