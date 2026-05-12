# Claude Platform on AWS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Claude Platform on AWS (`aws-external-anthropic.{region}.api.aws`) as a second test provider alongside Amazon Bedrock, run the same 57 contract tests across both, and produce a unified 2D comparison matrix.

**Architecture:** Provider abstraction module (`providers/`) with alias-based model identification. `client.py` becomes a thin backward-compat wrapper. `run_all.py` gains a `--providers` flag and emits a 2D nested matrix (`{provider: {alias: payload}}`) with a 4-section markdown report including a cross-provider diff section.

**Tech Stack:** Python 3.9+, `anthropic` SDK (`AnthropicBedrock` for Bedrock, `Anthropic` direct for CPaws). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-12-claude-platform-on-aws-design.md`

---

## File Structure

### Created
- `providers/__init__.py` — factory `make_client(provider)` + `resolve_model(provider, alias)`
- `providers/bedrock.py` — Bedrock client construction (relocated from `client.py`)
- `providers/cpaws.py` — Claude Platform on AWS client construction (new)

### Modified
- `client.py` — thin wrapper, delegates to `providers.make_client("bedrock")` for backward compat
- `config.py` — adds `PROVIDERS`, `MODEL_ALIASES`, redefines `ALL_MODELS` as alias list
- `run_all.py` — `--providers` flag, 2D matrix loop, per-provider tokens, 4-section markdown
- `.env.example` — adds `ANTHROPIC_AWS_API_KEY`, `ANTHROPIC_AWS_WORKSPACE_ID`, `CPAWS_REGION`
- `verify.sh` — cost notice mentions both Bedrock and AWS Marketplace billing
- `docs/architecture.md` — adds provider section explaining the two surfaces
- `tests/CLAUDE.md` — endpoint scope updated to include CPaws
- `CLAUDE.md` (root) — env vars + provider list + key commands section
- `CHANGELOG.md` — entry for the integration

### Untouched (per design Non-goals)
- `tests/<cat>/test_*.py` — no test body changes
- `tests/_base.py` — `is_unsupported_tool_rejection` extension deferred to optional P4
- `scripts/` — no probe updates

---

## Task 1: Create providers/ package with Bedrock client

**Files:**
- Create: `providers/__init__.py`
- Create: `providers/bedrock.py`

- [ ] **Step 1: Create `providers/` package directory and empty init**

```bash
mkdir -p providers
```

Then create `providers/__init__.py` with placeholder content (will be filled in Task 4):

```python
"""Provider abstraction — factory and model-alias resolver."""
```

- [ ] **Step 2: Create `providers/bedrock.py`**

```python
"""Bedrock provider — AnthropicBedrock client using AWS_BEARER_TOKEN_BEDROCK."""
import os
import sys
from anthropic import AnthropicBedrock


def make_client(region: str) -> AnthropicBedrock:
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("ERROR: AWS_BEARER_TOKEN_BEDROCK not set.", file=sys.stderr)
        sys.exit(2)
    return AnthropicBedrock(aws_region=region)
```

- [ ] **Step 3: Verify import works**

Run:
```bash
python3 -c "from providers.bedrock import make_client; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add providers/__init__.py providers/bedrock.py
git commit -m "feat(providers): scaffold providers package with bedrock client"
```

---

## Task 2: Add CPaws client

**Files:**
- Create: `providers/cpaws.py`

- [ ] **Step 1: Create `providers/cpaws.py`**

```python
"""Claude Platform on AWS provider — Anthropic SDK with custom base_url and
workspace API key authentication.

Endpoint: https://aws-external-anthropic.{region}.api.aws
Auth: ANTHROPIC_AWS_API_KEY → sent as x-api-key
Required header: anthropic-workspace-id (from ANTHROPIC_AWS_WORKSPACE_ID)
"""
import os
import sys
from anthropic import Anthropic


def make_client(region: str) -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    if not api_key:
        print("ERROR: ANTHROPIC_AWS_API_KEY not set.", file=sys.stderr)
        sys.exit(2)
    if not workspace_id:
        print("ERROR: ANTHROPIC_AWS_WORKSPACE_ID not set.", file=sys.stderr)
        sys.exit(2)
    return Anthropic(
        base_url=f"https://aws-external-anthropic.{region}.api.aws",
        api_key=api_key,
        default_headers={"anthropic-workspace-id": workspace_id},
    )
```

- [ ] **Step 2: Verify import works**

Run:
```bash
python3 -c "from providers.cpaws import make_client; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add providers/cpaws.py
git commit -m "feat(providers): add Claude Platform on AWS client"
```

---

## Task 3: Update config.py with MODEL_ALIASES and PROVIDERS

**Files:**
- Modify: `config.py`

- [ ] **Step 1: Replace `config.py` contents**

```python
"""Single source of truth for model + region + provider settings.

To validate a future model or add a provider, only this file needs to change.
"""
import os

# Providers supported by the suite.
PROVIDERS = ("bedrock", "cpaws")
DEFAULT_PROVIDER = "bedrock"

# Model aliases mapped to per-provider concrete model IDs.
# An alias is the human-friendly identifier used in matrix rows.
MODEL_ALIASES = {
    "opus-4-7": {
        "bedrock": "global.anthropic.claude-opus-4-7",
        "cpaws":   "claude-opus-4-7",
    },
    "opus-4-6": {
        "bedrock": "global.anthropic.claude-opus-4-6-v1",
        "cpaws":   "claude-opus-4-6",
    },
    "sonnet-4-6": {
        "bedrock": "global.anthropic.claude-sonnet-4-6",
        "cpaws":   "claude-sonnet-4-6",
    },
}

# All model aliases iterated in --all-models mode.
ALL_MODELS = list(MODEL_ALIASES.keys())

# Default single-model alias. BEDROCK_MODEL_ID env var still accepted for
# backward compatibility: if set, it is the concrete Bedrock model ID and
# overrides MODEL_ID resolution for single-model bedrock runs.
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-opus-4-7")

# Region used by both providers (CPaws also honors CPAWS_REGION).
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")

# Default token budget for short probes.
DEFAULT_MAX_TOKENS = 256

# Beta headers required for specific features.
BETA_1M_CONTEXT = "context-1m-2025-08-07"
BETA_PDF_DOCUMENTS = "pdfs-2024-09-25"
BETA_INTERLEAVED_THINKING = "interleaved-thinking-2025-05-14"

# Features known to be Anthropic-direct only (skipped on Bedrock).
BEDROCK_UNSUPPORTED = {
    "files_api",
    "message_batches",
    "admin_api",
    "server_tool_web_search",
    "server_tool_code_execution",
    "server_tool_memory",
    "computer_use",
    "mcp_connector",
}
```

- [ ] **Step 2: Verify imports**

Run:
```bash
python3 -c "
from config import PROVIDERS, MODEL_ALIASES, ALL_MODELS, MODEL_ID, REGION
assert PROVIDERS == ('bedrock', 'cpaws')
assert 'opus-4-7' in MODEL_ALIASES
assert MODEL_ALIASES['opus-4-7']['bedrock'] == 'global.anthropic.claude-opus-4-7'
assert MODEL_ALIASES['opus-4-7']['cpaws'] == 'claude-opus-4-7'
assert ALL_MODELS == ['opus-4-7', 'opus-4-6', 'sonnet-4-6']
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add config.py
git commit -m "feat(config): add PROVIDERS and MODEL_ALIASES, ALL_MODELS becomes alias list"
```

---

## Task 4: Wire up providers/__init__.py factory and resolver

**Files:**
- Modify: `providers/__init__.py`

- [ ] **Step 1: Replace `providers/__init__.py` with the factory**

```python
"""Provider abstraction — factory and model-alias resolver.

A "provider" is an API surface that hosts Anthropic Claude:
  - "bedrock" → AnthropicBedrock against bedrock-runtime
  - "cpaws"   → Anthropic SDK against aws-external-anthropic

An "alias" is a human-friendly model identifier ("opus-4-7"). The resolver
maps (provider, alias) → concrete provider-specific model ID.
"""
import os

from config import MODEL_ALIASES, PROVIDERS, REGION


def make_client(provider: str):
    """Construct a client for the given provider.

    bedrock → uses config.REGION (AWS_REGION).
    cpaws   → uses CPAWS_REGION env, falls back to config.REGION.
    """
    if provider == "bedrock":
        from .bedrock import make_client as _make
        return _make(REGION)
    if provider == "cpaws":
        from .cpaws import make_client as _make
        cpaws_region = os.environ.get("CPAWS_REGION", REGION)
        return _make(cpaws_region)
    raise ValueError(
        f"unknown provider {provider!r}; valid: {list(PROVIDERS)}"
    )


def resolve_model(provider: str, alias: str) -> str:
    """Return the concrete model ID for (provider, alias)."""
    if provider not in PROVIDERS:
        raise ValueError(
            f"unknown provider {provider!r}; valid: {list(PROVIDERS)}"
        )
    mapping = MODEL_ALIASES.get(alias)
    if mapping is None:
        raise ValueError(
            f"unknown model alias {alias!r}; "
            f"valid: {list(MODEL_ALIASES.keys())}"
        )
    model_id = mapping.get(provider)
    if model_id is None:
        raise ValueError(
            f"alias {alias!r} not mapped for provider {provider!r}"
        )
    return model_id
```

- [ ] **Step 2: Verify resolver works**

Run:
```bash
python3 -c "
from providers import resolve_model
assert resolve_model('bedrock', 'opus-4-7') == 'global.anthropic.claude-opus-4-7'
assert resolve_model('cpaws',   'opus-4-7') == 'claude-opus-4-7'
assert resolve_model('cpaws',   'sonnet-4-6') == 'claude-sonnet-4-6'
try:
    resolve_model('bedrock', 'unknown-alias')
except ValueError as e:
    assert 'unknown model alias' in str(e)
else:
    raise AssertionError('expected ValueError for unknown alias')
try:
    resolve_model('made-up', 'opus-4-7')
except ValueError as e:
    assert 'unknown provider' in str(e)
else:
    raise AssertionError('expected ValueError for unknown provider')
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add providers/__init__.py
git commit -m "feat(providers): wire factory and resolver in providers/__init__.py"
```

---

## Task 5: Convert client.py to backward-compat wrapper

**Files:**
- Modify: `client.py`

- [ ] **Step 1: Replace `client.py` contents**

```python
"""Backward-compat shim — keep `from client import make_client` working.

New code should call `providers.make_client(provider)` directly.
"""
from providers import make_client as _make_client


def make_client():
    """Construct the default-provider client (Bedrock)."""
    return _make_client("bedrock")
```

- [ ] **Step 2: Verify backward-compat path works**

Run:
```bash
AWS_BEARER_TOKEN_BEDROCK=dummy python3 -c "
from client import make_client
c = make_client()
print(type(c).__name__)
"
```
Expected: `AnthropicBedrock`

(The dummy token bypasses the env-var check; we do not call the API.)

- [ ] **Step 3: Commit**

```bash
git add client.py
git commit -m "refactor(client): convert to thin wrapper delegating to providers.make_client"
```

---

## Task 6: Refactor run_all.py to use providers and accept --providers flag

**Files:**
- Modify: `run_all.py`

- [ ] **Step 1: Update imports in `run_all.py`**

Locate the top-of-file imports (around line 1-25). Add the providers import and update the config imports.

Find:
```python
from client import make_client
```
Replace with:
```python
from providers import make_client, resolve_model
```

Find:
```python
from config import ALL_MODELS, MODEL_ID, REGION
```
Replace with:
```python
from config import ALL_MODELS, DEFAULT_PROVIDER, MODEL_ALIASES, MODEL_ID, PROVIDERS, REGION
```

- [ ] **Step 2: Add `--providers` argument to argparse**

In `main()` (around line 446), locate:
```python
    ap.add_argument("--all-models", action="store_true",
                    help="Run tests for every model in config.ALL_MODELS and emit a matrix.")
```

Insert immediately after it:
```python
    ap.add_argument("--providers", nargs="*", default=None,
                    help=f"Providers to run against. Default: {DEFAULT_PROVIDER}. "
                         f"Valid: {list(PROVIDERS)}.")
```

- [ ] **Step 3: Add provider resolution helper**

Insert this helper near the other top-level helpers in `run_all.py` (after `_classify_kind`, before `_render_matrix_markdown`):

```python
def _resolve_providers(args_providers: list[str] | None) -> list[str]:
    """Return validated provider list; default to DEFAULT_PROVIDER if not set."""
    if not args_providers:
        return [DEFAULT_PROVIDER]
    for p in args_providers:
        if p not in PROVIDERS:
            print(f"ERROR: unknown provider {p!r}; valid: {list(PROVIDERS)}",
                  file=sys.stderr)
            sys.exit(2)
    return list(args_providers)
```

- [ ] **Step 4: Smoke test — argparse accepts the new flag**

Run:
```bash
python3 run_all.py --providers cpaws --list-json | head -3
```
Expected: JSON inventory output (no error).

```bash
python3 run_all.py --providers nope --list-json 2>&1 | head -2
```
Expected: error message mentioning `unknown provider 'nope'`.

- [ ] **Step 5: Commit**

```bash
git add run_all.py
git commit -m "feat(run_all): add --providers flag and provider resolution helper"
```

---

## Task 7: Refactor matrix-mode loop to iterate (provider × alias)

**Files:**
- Modify: `run_all.py`

- [ ] **Step 1: Replace the matrix-mode block in `main()`**

Locate the existing matrix branch in `run_all.py` (around line 471, `if args.all_models:`) and the closing of that block (around line 510). Replace the entire `if args.all_models:` block with the version below.

```python
    providers_list = _resolve_providers(args.providers)

    if args.all_models:
        print(f"Providers: {providers_list}")
        print(f"Aliases:   {ALL_MODELS}")
        matrix: dict[str, dict[str, dict]] = {p: {} for p in providers_list}
        per_run_tokens: dict[tuple[str, str], TokenAccumulator] = {}

        run_idx = 0
        total_runs = len(providers_list) * len(ALL_MODELS)
        for provider in providers_list:
            for alias in ALL_MODELS:
                run_idx += 1
                model_id = resolve_model(provider, alias)
                print(f"\n{'═' * 72}")
                print(f"RUN {run_idx}/{total_runs}: provider={provider}  "
                      f"alias={alias}  model_id={model_id}")
                print('═' * 72)
                run_tokens = TokenAccumulator()
                client_for_run = make_client(provider)
                wrap_client_with_tracker(client_for_run, run_tokens)
                wrap_client_with_tracker(client_for_run, tokens)
                payload = _run_one_model(
                    client_for_run, model_id, args, started_utc
                )
                if payload is not None:
                    payload["provider"] = provider
                    payload["alias"] = alias
                    matrix[provider][alias] = payload
                    per_run_tokens[(provider, alias)] = run_tokens

        all_pass = sum(
            p["totals"]["passed"]
            for prov in matrix.values()
            for p in prov.values()
        )
        all_total = sum(
            p["totals"]["total"]
            for prov in matrix.values()
            for p in prov.values()
        )
        n_runs = sum(len(v) for v in matrix.values())
        print(f"\n{'═' * 72}")
        print(f"MATRIX TOTAL: {all_pass}/{all_total} across {n_runs} runs")

        for (provider, alias), t in per_run_tokens.items():
            print()
            print(f"-- per-run tokens: {provider} / {alias} --")
            _print_token_summary(t)

        for provider in providers_list:
            print()
            print(f"== provider-wide tokens: {provider} ==")
            prov_tokens = TokenAccumulator()
            for (p, _a), t in per_run_tokens.items():
                if p == provider:
                    s = t.summary()
                    prov_tokens.calls += s["calls"]
                    prov_tokens.input += s["input_tokens"]
                    prov_tokens.output += s["output_tokens"]
                    prov_tokens.cache_create_5m += s["ephemeral_5m_input_tokens"]
                    prov_tokens.cache_create_1h += s["ephemeral_1h_input_tokens"]
                    prov_tokens.cache_create_total += s["cache_creation_input_tokens"]
                    prov_tokens.cache_read += s["cache_read_input_tokens"]
            _print_token_summary(prov_tokens)

        print()
        print("== matrix-wide tokens (all providers) ==")
        _print_token_summary(tokens)

        if not args.no_save:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            matrix_json = RESULTS_DIR / "matrix.json"
            matrix_md = RESULTS_DIR / "matrix.md"
            matrix_json.write_text(json.dumps(matrix, default=str, indent=2))
            matrix_md.write_text(_render_matrix_markdown(matrix))
            print(f"\nMatrix saved:\n  {matrix_json}\n  {matrix_md}")
        return 0 if all_pass == all_total else 1
```

- [ ] **Step 2: Update the single-model branch to honor `--providers`**

Find the single-model branch in `main()` (the block after the matrix branch, starting with `# Single-model run`). Replace:

```python
    # Single-model run
    print(f"Model:   {MODEL_ID}")
    payload = _run_one_model(client, MODEL_ID, args, started_utc)
```

With:

```python
    # Single-model run
    if len(providers_list) > 1:
        print("ERROR: single-model run accepts at most one --providers value. "
              "Use --all-models for multi-provider matrix.", file=sys.stderr)
        return 2
    single_provider = providers_list[0]
    if single_provider == "bedrock":
        single_model_id = MODEL_ID
    else:
        single_alias = ALL_MODELS[0]
        single_model_id = resolve_model(single_provider, single_alias)
    print(f"Provider: {single_provider}")
    print(f"Model:    {single_model_id}")
    client = make_client(single_provider)
    wrap_client_with_tracker(client, tokens)
    payload = _run_one_model(client, single_model_id, args, started_utc)
    if payload is not None:
        payload["provider"] = single_provider
```

Note: remove the earlier `client = make_client()` + `wrap_client_with_tracker(client, tokens)` lines that lived above the matrix branch (around line 465-467) — they are now redundant since both branches construct their own clients after provider resolution. Move `tokens = TokenAccumulator()` to remain before both branches.

- [ ] **Step 3: Smoke test (syntax + flag wiring only — no real API call)**

Run:
```bash
python3 run_all.py --providers bedrock --list-json | head -3
```
Expected: JSON inventory.

```bash
python3 run_all.py --providers bedrock cpaws --list-json | head -3
```
Expected: JSON inventory (no error from accepting multiple providers).

- [ ] **Step 4: Commit**

```bash
git add run_all.py
git commit -m "feat(run_all): iterate (provider × alias) in matrix mode, nest matrix.json"
```

---

## Task 8: Update _render_matrix_markdown for nested 2D matrix

**Files:**
- Modify: `run_all.py`

- [ ] **Step 1: Replace `_render_matrix_markdown` signature and body**

Locate `_render_matrix_markdown` (around line 359). Replace the entire function with:

```python
def _render_matrix_markdown(matrix: dict[str, dict[str, dict]]) -> str:
    """Render a 2D matrix payload {provider: {alias: payload}}.

    Layout:
      1. Per-provider × per-model totals (single overview table)
      2. Test × Model matrix per provider (sub-section per provider)
      3. Cross-provider differences (same (test, alias), provider labels differ)
      4. Inter-model differences per provider
    """
    lines: list[str] = []
    lines.append("# Bedrock × Anthropic API — provider × model matrix")
    lines.append("")

    flat_runs = [
        (provider, alias, payload)
        for provider, by_alias in matrix.items()
        for alias, payload in by_alias.items()
    ]
    if not flat_runs:
        lines.append("(empty matrix)")
        return "\n".join(lines)

    first = flat_runs[0][2]
    lines.append(f"- **Region**: `{first['region']}`")
    lines.append(f"- **Started (UTC)**: {first['started_utc']}")
    lines.append(f"- **Providers**: {list(matrix.keys())}")
    lines.append(f"- **Total runs**: {len(flat_runs)}")
    lines.append("")

    # Section 1: Per-provider × per-model totals.
    lines.append("## Per-provider × per-model totals")
    lines.append("")
    lines.append("| Provider | Model | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail | Total |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for provider, alias, payload in flat_runs:
        counts = {"behavioral": 0, "rejected": 0, "mixed": 0, "fail": 0}
        for c in payload["categories"].values():
            for t in c["tests"]:
                counts[_classify_kind(t)] += 1
        total = payload["totals"]["total"]
        lines.append(
            f"| `{provider}` | `{alias}` | {counts['behavioral']} | "
            f"{counts['rejected']} | {counts['mixed']} | "
            f"{counts['fail']} | {total} |"
        )
    lines.append("")

    # Build a lookup keyed by (provider, alias) and (test_name, alias).
    # kind_at[(provider, alias)][test_name] = classification kind
    kind_at: dict[tuple[str, str], dict[str, str]] = {}
    test_categories: dict[str, str] = {}
    for provider, alias, payload in flat_runs:
        bucket = kind_at.setdefault((provider, alias), {})
        for cat, c in payload["categories"].items():
            for t in c["tests"]:
                bucket[t["name"]] = _classify_kind(t)
                test_categories[t["name"]] = cat

    # Section 2: Test × Model matrix per provider.
    lines.append("## Test × Model matrix")
    lines.append("")
    for provider, by_alias in matrix.items():
        lines.append(f"### `{provider}`")
        lines.append("")
        aliases = list(by_alias.keys())
        by_cat: dict[str, list[str]] = defaultdict(list)
        for tname, cat in test_categories.items():
            by_cat[cat].append(tname)
        for cat in sorted(by_cat.keys()):
            lines.append(f"#### `{cat}`")
            lines.append("")
            header = "| Test | " + " | ".join(f"`{a}`" for a in aliases) + " |"
            sep = "| --- | " + " | ".join(":---:" for _ in aliases) + " |"
            lines.append(header)
            lines.append(sep)
            for tname in sorted(by_cat[cat]):
                row = [f"`{tname}`"]
                for a in aliases:
                    k = kind_at.get((provider, a), {}).get(tname, "fail")
                    row.append(_icon_for(k))
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    # Section 3: Cross-provider differences.
    lines.append("## Cross-provider differences")
    lines.append("")
    providers_seen = list(matrix.keys())
    if len(providers_seen) < 2:
        lines.append("(only one provider in this run — no cross-provider diff)")
        lines.append("")
    else:
        all_aliases = sorted({alias for by_alias in matrix.values() for alias in by_alias})
        diffs: list[tuple[str, str, dict[str, str]]] = []
        for tname in sorted(test_categories):
            for alias in all_aliases:
                kinds_for_pair = {
                    p: kind_at.get((p, alias), {}).get(tname)
                    for p in providers_seen
                    if (p, alias) in kind_at
                }
                if len(kinds_for_pair) < 2:
                    continue
                if len(set(kinds_for_pair.values())) > 1:
                    diffs.append((tname, alias, kinds_for_pair))
        if not diffs:
            lines.append("All (test, alias) pairs agree across providers.")
            lines.append("")
        else:
            lines.append(
                f"{len(diffs)} (test, alias) pair(s) where providers disagree:"
            )
            lines.append("")
            header = "| Test | Alias | " + " | ".join(f"`{p}`" for p in providers_seen) + " |"
            sep = "| --- | --- | " + " | ".join(":---:" for _ in providers_seen) + " |"
            lines.append(header)
            lines.append(sep)
            for tname, alias, kinds in diffs:
                row = [f"`{tname}`", f"`{alias}`"]
                for p in providers_seen:
                    k = kinds.get(p, "fail")
                    row.append(_icon_for(k) if k else "·")
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    # Section 4: Inter-model differences per provider.
    lines.append("## Inter-model differences (within each provider)")
    lines.append("")
    for provider, by_alias in matrix.items():
        aliases = list(by_alias.keys())
        if len(aliases) < 2:
            continue
        lines.append(f"### `{provider}`")
        lines.append("")
        per_test: dict[str, dict[str, str]] = {}
        for alias in aliases:
            for tname, k in kind_at.get((provider, alias), {}).items():
                per_test.setdefault(tname, {})[alias] = k
        diffs = [
            (tname, kinds)
            for tname, kinds in per_test.items()
            if len(set(kinds.values())) > 1
        ]
        if not diffs:
            lines.append("All tests agree across models.")
            lines.append("")
            continue
        lines.append(f"{len(diffs)} test(s) where models disagree:")
        lines.append("")
        header = "| Test | " + " | ".join(f"`{a}`" for a in aliases) + " |"
        sep = "| --- | " + " | ".join(":---:" for _ in aliases) + " |"
        lines.append(header)
        lines.append(sep)
        for tname, kinds in sorted(diffs):
            row = [f"`{tname}`"]
            for a in aliases:
                k = kinds.get(a, "fail")
                row.append(f"{_icon_for(k)} {k}")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 2: Smoke test the renderer with a synthetic matrix**

Run:
```bash
python3 -c "
from run_all import _render_matrix_markdown
sample = {
    'bedrock': {
        'opus-4-7': {
            'region': 'ap-northeast-2',
            'started_utc': '2026-05-12T00:00:00Z',
            'totals': {'total': 2, 'passed': 1},
            'categories': {
                'caching': {'tests': [
                    {'name': 't1', 'ok': True,  'info': {'contract': 'supported'}},
                    {'name': 't2', 'ok': True,  'info': {'contract': 'rejected'}},
                ]},
            },
        },
    },
    'cpaws': {
        'opus-4-7': {
            'region': 'us-east-1',
            'started_utc': '2026-05-12T00:00:00Z',
            'totals': {'total': 2, 'passed': 1},
            'categories': {
                'caching': {'tests': [
                    {'name': 't1', 'ok': True,  'info': {'contract': 'supported'}},
                    {'name': 't2', 'ok': False, 'info': {'contract': 'accepted_unexpectedly'}},
                ]},
            },
        },
    },
}
md = _render_matrix_markdown(sample)
assert '## Per-provider × per-model totals' in md
assert '## Cross-provider differences' in md
assert 't2' in md
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add run_all.py
git commit -m "feat(run_all): render 4-section markdown for 2D provider × alias matrix"
```

---

## Task 9: Add provider field to single-model latest.json output

**Files:**
- Modify: `run_all.py`

- [ ] **Step 1: Confirm Task 7 already attaches `payload['provider']` in the single-model branch**

This was completed in Task 7 Step 2. No additional code change here — the purpose of Task 9 is the verification + commit gate for backward-compat readers.

- [ ] **Step 2: Read-back smoke test of payload shape**

Run:
```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
# Synthesize a payload to confirm json roundtrip preserves provider.
payload = {
    'provider': 'cpaws',
    'started_utc': '2026-05-12T00:00:00Z',
    'region': 'us-east-1',
    'model': 'claude-opus-4-7',
    'totals': {'total': 0, 'passed': 0},
    'categories': {},
}
roundtrip = json.loads(json.dumps(payload))
assert roundtrip['provider'] == 'cpaws'
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit** (no-op if Task 7 commit already covered it — skip)

```bash
git status
# If clean, skip. Otherwise:
git add run_all.py
git commit -m "feat(run_all): include provider field in single-model payload"
```

---

## Task 10: Smoke run end-to-end with bedrock-only matrix

**Files:**
- (no changes — run-only verification)

- [ ] **Step 1: Run a bedrock-only matrix with a single fast test**

Run:
```bash
python3 run_all.py --providers bedrock --all-models --only-tests messages_create
```
Expected:
- Console shows 3 RUN headers (one per alias).
- `results/matrix.json` is written and parses as `{"bedrock": {"opus-4-7": {...}, "opus-4-6": {...}, "sonnet-4-6": {...}}}`.
- `results/matrix.md` contains all 4 sections; "Cross-provider differences" section shows "(only one provider in this run — no cross-provider diff)".

- [ ] **Step 2: Sanity-check the JSON shape**

Run:
```bash
python3 -c "
import json
m = json.load(open('results/matrix.json'))
assert list(m.keys()) == ['bedrock']
assert set(m['bedrock'].keys()) == {'opus-4-7', 'opus-4-6', 'sonnet-4-6'}
for alias, payload in m['bedrock'].items():
    assert payload['provider'] == 'bedrock'
    assert payload['alias'] == alias
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit only if generated artifacts should be checked in**

This step intentionally does not commit `results/matrix.{json,md}` — those are generated artifacts. Confirm `git status` shows them as either ignored or untracked and skip.

```bash
git status results/
```

---

## Task 11: Update .env.example with CPaws variables

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Append CPaws block to `.env.example`**

Find the line:
```
CLAUDE_NOTIFY_WEBHOOK=
```

After that line, append:

```
# ── Claude Platform on AWS ─────────────────────────────────────────────
# Required to run --providers cpaws. Issued from the AWS Console under
# Claude Platform on AWS → API keys. The workspace ID is shown on the
# Workspaces page. Both must belong to the AWS-connected Anthropic org.
# Format of API key: starts with "sk-ant-".
ANTHROPIC_AWS_API_KEY=sk-ant-...replace-me
ANTHROPIC_AWS_WORKSPACE_ID=wrkspc_01ABCDEFGHIJKLMN

# Optional — region for the CPaws endpoint. Falls back to AWS_REGION.
# CPaws workspaces are provisioned per region; if your workspace lives
# in us-east-1, set this even when AWS_REGION points elsewhere.
CPAWS_REGION=us-east-1
```

- [ ] **Step 2: Verify file parses (no shell syntax error)**

Run:
```bash
bash -n .env.example && echo "OK"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs(env): add ANTHROPIC_AWS_API_KEY / WORKSPACE_ID / CPAWS_REGION"
```

---

## Task 12: Update verify.sh cost notice to mention both providers

**Files:**
- Modify: `verify.sh`

- [ ] **Step 1: Locate the existing cost/token notice block**

Run:
```bash
grep -n -i "cost\|token\|billing\|warning" verify.sh | head -20
```

Identify the user-facing notice that warns about token usage and credentials. The exact line numbers depend on the current state of `verify.sh`.

- [ ] **Step 2: Extend the notice to mention CPaws billing**

In the section where the script announces required env vars (the Bedrock bearer token block), insert a parallel block for CPaws. Use this pattern (adapt to the existing notice's wording):

```bash
# Inside the env-var validation section of verify.sh, alongside the
# existing AWS_BEARER_TOKEN_BEDROCK check, append:

if [ "${PROVIDERS:-bedrock}" = *"cpaws"* ] || [ "${1:-}" = "matrix" ]; then
  if [ -z "${ANTHROPIC_AWS_API_KEY:-}" ] || [ -z "${ANTHROPIC_AWS_WORKSPACE_ID:-}" ]; then
    echo "WARNING: Claude Platform on AWS requested but ANTHROPIC_AWS_API_KEY"
    echo "         or ANTHROPIC_AWS_WORKSPACE_ID is not set. CPaws runs will fail."
    echo "         Billing for CPaws is via AWS Marketplace, separate from Bedrock."
  fi
fi
```

And in the user-facing cost notice (the multi-line `cat <<EOF` or `echo` block that warns about costs), append:

```
NOTE: Running matrix mode with both providers (--providers bedrock cpaws)
charges BOTH bills:
  - Bedrock          → standard Bedrock invoke pricing
  - Claude Platform  → AWS Marketplace subscription pricing
A full matrix is ~ 2x the single-provider cost.
```

- [ ] **Step 3: Lint the shell script**

Run:
```bash
bash -n verify.sh && echo "OK"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add verify.sh
git commit -m "docs(verify): warn that CPaws billing is separate (AWS Marketplace)"
```

---

## Task 13: Update docs/architecture.md with provider section

**Files:**
- Modify: `docs/architecture.md`

- [ ] **Step 1: Identify the architecture sections**

Run:
```bash
grep -n "^#\|^##" docs/architecture.md | head -30
```

- [ ] **Step 2: Add a "Providers" section after the existing Overview**

Append (or insert after the Overview/Components section, depending on the file's structure) the following bilingual block — the project convention is `# English` followed by `# 한국어` mirror H1s per `project_results_bilingual_doc_convention`. If `architecture.md` is single-language, insert in the existing language only.

```markdown
## Providers

The suite supports two AWS-hosted Anthropic Claude surfaces, switchable
via the `--providers` flag on `run_all.py`:

| Provider | Endpoint | Auth | SDK class | Model ID example |
| --- | --- | --- | --- | --- |
| `bedrock` | `bedrock-runtime.{region}.amazonaws.com` | `AWS_BEARER_TOKEN_BEDROCK` (Bearer / ABSK) | `anthropic.AnthropicBedrock` | `global.anthropic.claude-opus-4-7` |
| `cpaws` | `aws-external-anthropic.{region}.api.aws` | `ANTHROPIC_AWS_API_KEY` (x-api-key) + `anthropic-workspace-id` header | `anthropic.Anthropic` (custom base_url) | `claude-opus-4-7` |

Mantle (`bedrock-mantle.{region}.api.aws`) is intentionally out of scope; see
`results/docs_vs_reality.md` for the reasoning.

Model aliases (`opus-4-7`, `opus-4-6`, `sonnet-4-6`) are the unit of matrix
rows. The concrete provider-specific model ID is resolved at run time by
`providers.resolve_model(provider, alias)` from `config.MODEL_ALIASES`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.md
git commit -m "docs(arch): add Providers section explaining bedrock vs cpaws surfaces"
```

---

## Task 14: Update tests/CLAUDE.md, CLAUDE.md, CHANGELOG.md

**Files:**
- Modify: `tests/CLAUDE.md`
- Modify: `CLAUDE.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update `tests/CLAUDE.md` endpoint scope**

Find the line in `tests/CLAUDE.md`:
```
The contract suite. Each subdirectory mirrors a category from Anthropic's
"Build with Claude" documentation. Each `test_*.py` encodes one runtime
contract that `run_all.py` exercises against `bedrock-runtime` Invoke API.
```

Replace with:

```
The contract suite. Each subdirectory mirrors a category from Anthropic's
"Build with Claude" documentation. Each `test_*.py` encodes one runtime
contract that `run_all.py` exercises against one of the supported provider
surfaces (currently `bedrock` and `cpaws`). Tests themselves are
provider-agnostic — `run(client, model)` accepts whichever client/model the
runner injects.
```

- [ ] **Step 2: Update root `CLAUDE.md` Tech Stack and Key Commands**

Find in `CLAUDE.md` (root) the Tech Stack section's `**Auth**: AWS Bedrock API Key via AWS_BEARER_TOKEN_BEDROCK (Bearer)` line.

Replace with:
```
- **Auth (bedrock)**: AWS Bedrock API Key via `AWS_BEARER_TOKEN_BEDROCK` (Bearer)
- **Auth (cpaws)**: Workspace API key via `ANTHROPIC_AWS_API_KEY` (x-api-key)
  + `ANTHROPIC_AWS_WORKSPACE_ID` (required header)
```

In the same file, find the Key Commands section and add the new provider commands. After the existing `# 3-model matrix` block, insert:

```bash
# Multi-provider matrix (bedrock × cpaws × 3 models = 6 runs)
python3 run_all.py --providers bedrock cpaws --all-models

# Single CPaws run (uses MODEL_ALIASES[0] = opus-4-7)
python3 run_all.py --providers cpaws
```

Also, find the env vars section near the bottom:
```
Required env: `AWS_BEARER_TOKEN_BEDROCK`. Optional: `AWS_REGION`
(default `ap-northeast-2`), `BEDROCK_MODEL_ID`.
```

Replace with:
```
Required env:
- `AWS_BEARER_TOKEN_BEDROCK` (for `--providers bedrock`, default)
- `ANTHROPIC_AWS_API_KEY` and `ANTHROPIC_AWS_WORKSPACE_ID` (for `--providers cpaws`)

Optional env:
- `AWS_REGION` (default `ap-northeast-2`) — shared between providers
- `CPAWS_REGION` — overrides `AWS_REGION` for CPaws only
- `BEDROCK_MODEL_ID` — single-model run override for bedrock
```

- [ ] **Step 3: Append CHANGELOG entry**

Find the top of `CHANGELOG.md`. Insert a new entry block above the existing first entry. Use the project's existing entry format (read the first few entries to match style — usually `## [Unreleased]` or a date-versioned section).

Example block (adapt to existing format):

```markdown
## 2026-05-12 — Claude Platform on AWS provider integration

### Added
- `providers/` module abstracting Bedrock and Claude Platform on AWS as
  interchangeable test targets (`bedrock`, `cpaws`).
- `config.MODEL_ALIASES` mapping human aliases (`opus-4-7`, `opus-4-6`,
  `sonnet-4-6`) to per-provider concrete model IDs.
- `run_all.py --providers` flag (multi-value). Default behavior unchanged.
- Matrix markdown now includes a "Cross-provider differences" section.
- Env vars: `ANTHROPIC_AWS_API_KEY`, `ANTHROPIC_AWS_WORKSPACE_ID`,
  `CPAWS_REGION` (optional).

### Changed (breaking)
- `results/matrix.{json,md}` schema is now 2D nested
  (`{provider: {alias: payload}}`). Past snapshots (`matrix-2026-05-04.*`)
  remain on disk unchanged.
- `config.ALL_MODELS` is now a list of aliases, not concrete Bedrock IDs.

### Documentation
- `docs/architecture.md` gains a "Providers" section.
- `tests/CLAUDE.md` endpoint scope updated to include CPaws.
```

- [ ] **Step 4: Smoke check — all three files parse cleanly**

Run:
```bash
python3 -c "
for p in ['CLAUDE.md', 'tests/CLAUDE.md', 'CHANGELOG.md']:
    with open(p) as f:
        body = f.read()
    assert len(body) > 0, p
    print(p, len(body), 'bytes')
"
```
Expected: three lines, all non-empty.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md tests/CLAUDE.md CHANGELOG.md
git commit -m "docs: reflect cpaws provider integration in project docs and CHANGELOG"
```

---

## Self-Review

The author of this plan reviewed it against the spec
`docs/superpowers/specs/2026-05-12-claude-platform-on-aws-design.md` with
the following result:

1. **Spec coverage**:
   - §1 Architecture (providers/, client.py wrapper, config.MODEL_ALIASES) → Tasks 1-5.
   - §2 Runner (`--providers`, 2D matrix, 4-section markdown, per-provider tokens) → Tasks 6-10.
   - §3 Phased delivery P3 (env, verify.sh, architecture.md, tests/CLAUDE.md, CLAUDE.md, CHANGELOG) → Tasks 11-14.
   - Phase P4 (`is_unsupported_tool_rejection` extension, `results/cpaws_findings.md`) intentionally **deferred** — listed as optional in the spec, treated as out-of-plan here. To be authored as a follow-up plan after the first real CPaws matrix run produces empirical data.

2. **Placeholder scan**: No `TBD`, `TODO`, "implement later", or "similar to Task N" references. All code blocks are concrete. The single ambiguous step (Task 12 Step 1 says "identify the existing notice's wording") is unavoidable without reading the current `verify.sh`; the engineer reads it then applies the patch shown.

3. **Type consistency**:
   - `providers.make_client(provider)` — single string arg, consistent across Tasks 4, 5, 7.
   - `providers.resolve_model(provider, alias)` — two strings, consistent across Tasks 4, 7.
   - `MODEL_ALIASES` keyed by alias → `{provider: model_id}` — consistent across Tasks 3, 4, 7, 8.
   - Matrix shape `dict[str, dict[str, dict]]` — consistent across Tasks 7, 8.
   - `payload["provider"]` and `payload["alias"]` fields — added in Task 7, validated in Task 10.

4. **Smoke verification at each phase**:
   - P1 end (Task 6): argparse smoke + `--list-json` parse.
   - P2 end (Task 10): real run on bedrock single-test, JSON shape check.
   - P3 end (Task 14): docs files non-empty.
   - A real CPaws end-to-end run requires live `ANTHROPIC_AWS_API_KEY` + workspace; not part of this plan's verification because credentials are an environment concern.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-12-claude-platform-on-aws.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Best when you want to inspect intermediate diffs and intervene if a task drifts.

2. **Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Best when you want continuous progress in one shot.

Which approach?


