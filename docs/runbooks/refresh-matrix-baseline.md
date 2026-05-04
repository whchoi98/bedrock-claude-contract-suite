# Runbook: Refresh contract matrix baseline

## Purpose

Run the full Bedrock × Anthropic verification matrix and freeze the
result as a dated baseline that future runs can be compared against.

## When to use

- After Bedrock or Anthropic announces a model update.
- After adding a new test category.
- After rewriting a contract test (e.g. structured outputs, strict tool
  use) — verify the new contract before publishing.
- Quarterly drift check.

## Prerequisites

```bash
[ -n "$AWS_BEARER_TOKEN_BEDROCK" ] || { echo "TOKEN MISSING"; exit 1; }
[ -n "${AWS_REGION:-ap-northeast-2}" ] && echo "REGION OK"
python3 -c "import anthropic; print('SDK', anthropic.__version__)"
```

## Procedure

### Step 1: Pre-flight

```bash
git status                                  # if applicable
ls -la results/matrix.{json,md}             # check current baseline mtime
```

If the current baseline is fresh (< 24h) and you're not investigating a
specific change, skip — no refresh needed.

### Step 2: Run the matrix

```bash
python3 run_all.py --all-models 2>&1 | tee /tmp/matrix-run-$(date -u +%Y%m%d).log
```

Expected output: per-category summary per model, `MATRIX TOTAL: X/Y`,
and per-model + matrix-wide token usage summary.

**Cost**: ~$5 USD per full run (see `verify.sh -h` for current
estimate). If matrix run is interrupted, partial state is in
`results/matrix.{json,md}` and may be inconsistent — re-run to overwrite.

### Step 3: Compare against previous baseline

```bash
DIFF_TARGETS=$(ls -t results/matrix-*.json 2>/dev/null | head -2)
diff <(jq '.["global.anthropic.claude-opus-4-7"].categories' results/matrix.json) \
     <(jq '.["global.anthropic.claude-opus-4-7"].categories' $(echo "$DIFF_TARGETS" | tail -1))
```

Look for:
- Any test whose `ok` value changed
- Any test whose `info.contract` value changed (e.g. "supported" →
  "rejected_..." or vice versa)

### Step 4: Investigate any new ❌

For each ❌ NOT in `results/docs_vs_reality.md` "real platform variance"
list:

1. Re-run that test only:
   `python3 run_all.py --only-tests <name>`
2. Inspect the captured `info` for the failing model.
3. Decide: test bug (fix the test) vs platform regression (document in
   `docs_vs_reality.md`).

### Step 5: Snapshot and document

```bash
DATE=$(date -u +%Y-%m-%d)
cp results/matrix.json   results/matrix-${DATE}.json
cp results/matrix.md     results/matrix-${DATE}.md
```

Update the "Last reviewed" line at the bottom of:
- `results/prompt_caching_verified.md`
- `results/docs_vs_reality.md`

### Step 6: Commit / tag (if git initialized)

Per the `release` skill, decide MAJOR/MINOR/PATCH and tag accordingly.

## Verification

- `ls -la results/matrix-*.json` shows the new dated snapshot.
- `tail -1 results/docs_vs_reality.md` shows the updated review date.
- Cost summary printed at end of `run_all.py` matches the verify.sh
  notice within ±10%.

## Rollback

This procedure only adds dated snapshots; the live `matrix.{json,md}`
is overwritten in place. To revert to a previous baseline:

```bash
cp results/matrix-YYYY-MM-DD.json results/matrix.json
cp results/matrix-YYYY-MM-DD.md   results/matrix.md
```

## References

- Root `CLAUDE.md` Key Commands
- `verify.sh` cost notice (top of file)
- `.claude/skills/release/SKILL.md`
