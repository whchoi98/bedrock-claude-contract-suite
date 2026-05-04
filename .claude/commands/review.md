---
description: Code review on current changes (test/probe code) with confidence-based filtering
allowed-tools: Read, Glob, Grep, Bash(git diff:*), Bash(git log:*)
---

# Code Review (verification suite)

Review the current code changes using the project's `code-review` skill.

## Step 1: Get Changes

- If $ARGUMENTS specifies files, review those.
- Otherwise, run `git diff` (or `git diff --cached` if no unstaged
  changes). If this isn't a git repo, fall back to listing recently
  modified files under `tests/`, `scripts/`, `results/`.

## Step 2: Apply code-review skill

Invoke the project's `code-review` skill — emphasis on:
- Contract integrity (NAME / DESCRIPTION / run signature, info.contract
  vocabulary)
- Reuse of `tests/_base` helpers (`text_of`, `usage_breakdown`,
  `is_unsupported_tool_rejection`)
- Cold-start salt for cache tests (see root CLAUDE.md Conventions)
- Strict assertions (no OR-fallback)

## Step 3: Score and Filter

Rate each issue 0-100. Only report issues with confidence ≥ 75.

## Step 4: Output

Present findings in structured format with `file_path:line` references.
If no high-confidence issues, confirm code meets standards.

## Error Recovery

### If no diff and not a git repo
List the 10 most recently modified .py files under `tests/`/`scripts/`/`results/`
and offer to review those.

### If CLAUDE.md missing
Cannot evaluate project guidelines without root `CLAUDE.md`. Suggest
running `/project-init:init-project` or creating one manually.
