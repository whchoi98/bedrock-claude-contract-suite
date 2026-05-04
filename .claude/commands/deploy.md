---
description: "Publish" a verified contract baseline (this project's release model)
allowed-tools: Read, Bash(python3 run_all.py:*), Bash(cp:*), Bash(ls:*)
---

# Deploy / Publish baseline

This project does not deploy code to a runtime. The "deploy" action is
publishing a verified contract baseline that downstream consumers (other
projects pinning to a specific Bedrock contract) can trust.

## Step 1: Pre-flight

1. Verify a clean matrix run was done within the last 24h
   (`results/matrix.json` mtime check).
2. Verify any ❌ items are documented as expected variance in
   `results/docs_vs_reality.md`.
3. Verify `results/prompt_caching_verified.md` and
   `results/docs_vs_reality.md` are up to date with the matrix.

## Step 2: Snapshot

```bash
DATE=$(date -u +%Y-%m-%d)
cp results/matrix.json   results/matrix-${DATE}.json
cp results/matrix.md     results/matrix-${DATE}.md
```

## Step 3: Update Findings Doc Headers

In each verified-finding doc, bump the "Last reviewed" line to the
snapshot date.

## Step 4: Tag (if git initialized)

Determine version per the `release` skill (MAJOR if any contract verdict
flipped, MINOR if scope expanded, PATCH otherwise).

```bash
git tag -a vX.Y.Z -m "Contract baseline vX.Y.Z (matrix-${DATE})"
```

## Step 5: Summary

Display:

- Snapshot files written
- Version assigned and rationale
- Per-model contract verdicts at this baseline
- What changed since the previous baseline (if any)

## Error Recovery

### Stale matrix
If `results/matrix.json` is older than 24h, refuse to publish and
suggest running `/test-all` first.

### Undocumented ❌
If new ❌ items appear, refuse to publish until either (a) the test bug
is fixed (per the `code-review` skill) or (b) the platform variance is
documented in `results/docs_vs_reality.md`.
