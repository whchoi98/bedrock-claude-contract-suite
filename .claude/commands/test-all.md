---
description: Run the full Bedrock × Anthropic verification matrix and report results
allowed-tools: Read, Bash(python3 run_all.py:*), Bash(./verify.sh:*), Bash(bash verify.sh:*), Glob
---

# Test All

Run the full Bedrock × Anthropic verification matrix.

## Step 1: Pre-flight

- Verify `AWS_BEARER_TOKEN_BEDROCK` is set. If not, prompt user (we do
  not echo or log token values).
- Verify `AWS_REGION` (defaults to `ap-northeast-2`).
- Display the cost notice from `verify.sh -h` so the user knows what's
  being committed (~$5 USD for the 3-model matrix run).

## Step 2: Run

Default: full 3-model matrix run with token tracking.

```bash
python3 run_all.py --all-models
```

If $ARGUMENTS specifies categories, limit scope:

```bash
python3 run_all.py --all-models --only $ARGUMENTS
```

## Step 3: Report

Present from the run output:

- Per-model passed / total counts
- Any ❌ failures with category, name, and one-line cause
- Token-usage summary: per-model + matrix-wide totals
- Approximate USD cost estimate

## Step 4: Compare against expected

Cross-reference with `results/docs_vs_reality.md`:

- Are any ❌ items NOT in the documented "real platform variance" list?
  Those are new contract changes worth investigating.
- Are any 🟢 items now ⛔, or vice versa? Flag for user attention —
  these may indicate Bedrock-side changes.

## Error Recovery

### Token missing
Prompt user to provide via `! export AWS_BEARER_TOKEN_BEDROCK=...` or
direct paste (we accept and use in-memory only).

### Specific test failure with unfamiliar error
- Capture full info dict from matrix.json for the failing test
- Compare against the test's expected `info.contract` shape
- If error message structure has changed, the test's matcher may need
  updating (see `is_unsupported_tool_rejection` for an example pattern)

### Many failures at once
Likely a Bedrock-side regression OR the network is intermittent.
1. Re-run a small subset: `python3 run_all.py --only caching`
2. If subset fails the same way, treat as platform-level signal
3. If subset passes, treat as flake — ignore single fails
