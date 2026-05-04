---
name: refactor
description: Refactor existing test/harness code to improve quality without changing behavior. Especially useful for promoting duplicated logic into tests/_base.py.
---

# Refactor Skill (verification suite)

Refactor existing code to improve quality without changing behavior.
Behavior preservation here means: the matrix result for every test must
remain unchanged before and after.

## Principles

- Improve structure without changing the contract a test encodes.
- Single Responsibility Principle (SRP).
- Remove duplicate code (DRY) — common pattern is lifting helpers into
  `tests/_base.py`.
- Small, incremental steps with verification via `python3 run_all.py`.

## Process

### 1. Analysis

- Identify the target code and which tests cover it.
- Map all callers: e.g. `_u()` may live in 4 files; lifting it requires
  updating each call site.
- Confirm the matrix result is currently green for the in-scope tests.

### 2. Plan

Present the refactoring plan to the user:
- What will change (helper hoist, name change, etc.)
- What will NOT change (info.contract values, ok status per model)
- Risk assessment (low/medium/high). Lifting pure helpers = low risk.

### 3. Execute

- Make changes in small, verifiable steps.
- Re-run only the affected category between steps:
  `python3 run_all.py --only caching`.
- Verify `info.contract` and `ok` values are byte-identical before/after
  by diffing matrix.json.

### 4. Verify

- Full matrix run: `python3 run_all.py --all-models`.
- Compare per-model passed/total counts.
- Compare `info.contract` for the touched tests across all 3 models.

## Common refactor patterns in this codebase

- **Helper hoist**: 3+ files share a private `_helper()` → move to
  `tests/_base.py`, import everywhere.
- **Constant deduplication**: SCHEMA / MODELS / REGION → import from
  `config.py` or the canonical test file.
- **Module-level hoist**: `"... " * 1500` recomputed on every call → make
  it a module-level constant.
- **Stringly-typed cleanup**: ad-hoc `info.contract` strings → consider
  hoisting into a Contract enum if usage grows past 10+ values.
