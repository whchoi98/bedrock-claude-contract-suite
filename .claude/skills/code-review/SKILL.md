---
name: code-review
description: Review changed test/probe code with confidence-based scoring; emphasizes the project's contract-encoding conventions (cold-start salt, strict assertions, model-divergent contracts).
---

# Code Review Skill (verification suite)

Review changed code with confidence-based scoring to filter false positives.
Tailored to this project's contract-encoding style: each test file pins a
runtime contract, so review focuses on whether the contract is encoded
correctly, not on generic style issues.

## Review Scope

By default, review unstaged changes from `git diff` (this project may not
be a git repo — fall back to recently-modified `tests/`/`scripts/`/`results/`
files). The user may specify different files or scope.

## Review Criteria — project-specific

### Contract integrity (HIGHEST priority)
- Does the test return `{"ok": bool, "info": dict, "error": str|None}` per
  the harness in `tests/_base.py`?
- Does it set `info.contract` to a string the runner classifier can map?
  (`"reject..."` → ⛔, anything else → 🟢)
- For cache-related tests: is a cold-start salt (`secrets.token_hex(8)`)
  embedded in the cached prefix? Without it, the test reads from prior
  state and silently passes.
- Is the assertion strict (single-condition) or does it use OR-fallback
  that masks contract drift?

### Reuse and harness primitives
- Does the file reimplement `text_of`, `usage_breakdown`, or
  `is_unsupported_tool_rejection` instead of importing from `tests._base`?
- Does it redeclare `MODELS` / `REGION` instead of importing from `config`?
- Does it call `AnthropicBedrock(...)` directly instead of `make_client()`?

### Bug detection
- Logic errors and null/undefined handling
- Race conditions (esp. in concurrent probes)
- Silent error swallowing (`except Exception`) — should be narrow

### Code quality
- Stringly-typed `info.contract` values without a vocabulary
- Narrative/changelog comments ("previous version", "now corrected")
- Hot-path string multiplications that should be module-level

## Confidence Scoring

Rate each issue 0-100. Only report issues with confidence ≥ 75.

## Output Format

For each issue:
### [CRITICAL|IMPORTANT] <issue title> (confidence: XX)
**File:** `path/to/file.py:line`
**Issue:** Clear description
**Guideline:** Reference to root `CLAUDE.md` Conventions section
**Fix:** Concrete code suggestion

If no high-confidence issues found, confirm code meets standards with brief
summary noting which conventions were verified.
