---
name: sync-docs
description: Synchronize project documentation (CLAUDE.md, README, results/*.md) with current code state. Especially useful after adding tests, changing model list, or after a Bedrock contract change is observed.
---

# Sync Docs Skill (verification suite)

Synchronize project documentation with current code state. This project
has multiple sources of truth that must stay aligned:

- Root `CLAUDE.md` — Tech Stack, Conventions, Key Commands
- `tests/<cat>/CLAUDE.md` — per-category role descriptions
- `README.md` — public overview, test inventory, findings summary
- `results/prompt_caching_verified.md` — prompt-caching contract reference
- `results/docs_vs_reality.md` — docs vs measured contract diff
- `docs/architecture.md` — system architecture
- `docs/bedrock-api-endpoints-comparison.md` — endpoint catalog

## Actions

### 1. Quality Assessment

Score each `CLAUDE.md` (0-100):
- Commands/workflows accurate (20 pts) — copy-paste runs?
- Conventions actionable (20 pts) — would a new dev follow them?
- Non-obvious patterns documented (15 pts) — esp. cold-start salt,
  contract classifier substring matching
- Conciseness (15 pts) — under 200 lines for module CLAUDE.md
- Currency (15 pts) — model list matches `config.ALL_MODELS`?
- Actionability (15 pts) — links to evidence files?

Anti-patterns:
- Over 500 lines (-15)
- Vague instructions ("update the test") (-10)
- Duplicated docs across files (-10)
- Stale model IDs (-15)
- Contains secrets (-20)

Output quality report with grades (A-F) BEFORE making changes.

### 2. Root CLAUDE.md Sync

- Verify `Key Commands` block matches actual `run_all.py` flags and
  `verify.sh` commands
- Verify `Tech Stack` matches imports in `client.py`/`config.py`
- Verify `Project Structure` tree matches actual `ls` output

### 3. Architecture Doc Sync

- `docs/architecture.md` should reflect current `tests/`/`scripts/`/
  `results/` layout
- Note any new probe scripts in §"Components"

### 4. Module CLAUDE.md Audit

- For every directory under `tests/`, `scripts/`, `results/`: ensure a
  `CLAUDE.md` exists
- Update existing module CLAUDE.md if recently-touched files have
  drifted from the documented role

### 5. Results Docs Audit

- Verify each "claim → evidence file" link in
  `results/docs_vs_reality.md` still resolves
- Verify TL;DR table in `results/prompt_caching_verified.md` matches
  current matrix.json

### 6. README.md Sync

- Update test inventory (categories with counts) to match actual
  directory layout
- Update Findings section to reference any new verified items

### 7. Report

Output before/after quality scores, anti-patterns detected, and a list
of all files touched.
