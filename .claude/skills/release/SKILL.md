---
name: release
description: Snapshot and tag a verified contract baseline. The "release" of this verification suite is the matrix.json + verified findings docs as a frozen artifact.
---

# Release Skill (verification suite)

This project doesn't ship code to users — it produces verified contract
artifacts. A "release" is freezing the current matrix + findings as a
named baseline that future runs can be compared against.

## Procedure

### 1. Pre-release Checks

- Verify working tree is clean: `git status`
- Run a fresh full matrix: `python3 run_all.py --all-models`
- Verify pass count and that the only ❌ are documented "real platform
  variance" items in `results/docs_vs_reality.md`
- Confirm token-usage summary lines up with the notice in `verify.sh`

### 2. Determine Version

- Review changes since last tag: `git log $(git describe --tags --abbrev=0)..HEAD --oneline`
- Apply semver-like rules:
  - **MAJOR**: A previously 🟢 contract flips to ⛔ (or vice versa) on at
    least one model in `ALL_MODELS`. This is a breaking change for
    callers reading the matrix.
  - **MINOR**: New test category added, or new model added to
    `ALL_MODELS`. Existing contracts unchanged.
  - **PATCH**: Test bug fixes (no contract change), refactors,
    documentation updates.

### 3. Snapshot Artifacts

- Copy the current matrix into a dated baseline:
  `cp results/matrix.json results/matrix-YYYY-MM-DD.json`
- Copy the latest single-model run if relevant.
- Update `results/prompt_caching_verified.md` and
  `results/docs_vs_reality.md` to reflect the version stamp at the
  bottom ("Last reviewed").

### 4. Update Changelog

Group changes by section:
- **Contract changes** — list each test whose verdict flipped
- **New tests** — list new files under `tests/`
- **Methodology** — list changes in `tests/_base.py` or run_all.py that
  affect how tests measure
- **Doc updates** — list new findings or corrections

### 5. Create Tag (if git is initialized)

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z — <one line summary>"
```

### 6. Summary

- Display version bump
- List key contract changes
- Note next monitoring steps (e.g. "re-run matrix after Bedrock model
  release X")
