# probes/ Module

## Role

Reusable Python library form of the contract suite. The same code that
`run_all.py` exercises is exposed here as importable functions so other
projects can run any probe against any Anthropic client (Bedrock, CPaws,
or Anthropic direct) without needing the runner.

`tests/<cat>/test_*.py` are thin shims that re-export from
`probes/<cat>/<name>.py`. **Edit code here, not in `tests/`.**

## Key Files

- **`_base.py`** — shared primitives (`Result`, `execute`, `text_of`,
  `usage_breakdown`, `is_unsupported_tool_rejection`). Import from
  `probes._base` in new code. `tests/_base.py` is a re-export shim for
  backward compatibility with `run_all.py`'s discovery path.
- **`__init__.py`** — auto-walks the category subpackages at import time
  and builds the `PROBES` catalog. Exposes `list_probes()`,
  `get_probe()`, `run_probe()` helpers.
- **`<category>/__init__.py`** — re-exports each submodule so
  `from probes.caching import cache_ttl_1h` works.
- **`<category>/<name>.py`** — one probe per file. Exposes `NAME`,
  `DESCRIPTION`, and `run(client, model) -> dict`.

## Probe contract (REQUIRED)

Every probe module MUST expose:

```python
NAME = "stable_short_id"           # used as catalog key suffix
DESCRIPTION = "what is verified"

def run(client, model) -> dict:
    return {
        "ok": bool,                # pass/fail per the probe's own assertion
        "info": {                  # surfaces in catalog; classifier reads contract
            "contract": "...",     # e.g. "supported" / "rejected" / "rejected_on_invoke_for_this_model"
            ...
        },
        "error": str | None,
    }
```

## Use from another project

```python
from probes import PROBES, list_probes, get_probe, run_probe

# Iterate the catalog
for key in list_probes(category="caching"):
    print(key, PROBES[key]["description"])

# Direct call
from probes.caching import cache_ttl_1h
result = cache_ttl_1h.run(client, "claude-opus-4-7")

# Lookup + call
run_probe("caching.cache_ttl_1h", client, "claude-opus-4-7")
```

## Naming rules

- Module name must be a valid Python identifier:
  - No reserved words (`async`/`await`/`match`/`case`) — suffix with
    `_client` for `client/`, `_` elsewhere
  - Cannot start with a digit — prefix with the category name
    (e.g. `1m_window.py` → `context_1m_window.py`)
- `NAME` constant stays the original short id (matrix rows use this).

## Provider-agnostic principle

A probe MUST NOT instantiate its own client. It accepts the `client`
that the runner injected (whichever provider). Tests that need an async
counterpart (`client/async_client.py`) detect provider via `isinstance`
and build the matching async client from env vars — see that file as the
canonical example.

## Rules

- **NEVER** hardcode `AnthropicBedrock` / `AnthropicAWS` / `Anthropic`
  in a probe — always use the injected `client`. The one exception
  (`client/async_client.py`) dispatches via `isinstance` to build the
  async twin of whatever sync client was passed.
- **NEVER** redeclare `MODELS` / `REGION` / `ALL_MODELS`. Import from
  `config`.
- **Cache probes** MUST embed `secrets.token_hex(8)` into the cached
  prefix. See ADR-001.
- **Strict assertions** — no OR-fallback that masks contract drift.
- **Model-divergent contracts** are encoded via adaptive `info.contract`
  values in a single probe. See
  `probes/messages/structured_outputs.py` for the pattern.
- **New category** → create `probes/<cat>/__init__.py` re-exports,
  add the corresponding `tests/<cat>/test_*.py` shims (or use
  `scripts/migrate_tests_to_probes.py` to regenerate).
