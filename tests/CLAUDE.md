# tests/ Module

## Role

The contract suite. Each subdirectory mirrors a category from Anthropic's
"Build with Claude" documentation. Each `test_*.py` encodes one runtime
contract that `run_all.py` exercises against one of the supported provider
surfaces (currently `bedrock` and `cpaws`). Tests themselves are
provider-agnostic — `run(client, model)` accepts whichever client/model the
runner injects.

## Key Files

- **`_base.py`** — shared harness primitives. ALL tests import from here:
  - `Result` dataclass + `execute()` defensive runner
  - `text_of(message)` — concatenate text blocks from a response
  - `usage_breakdown(usage)` — flatten `cache_creation` into a dict
  - `is_unsupported_tool_rejection(message, tool_type=None)` — match
    Bedrock's "not supported" / "Input tag does not match" rejection forms

## Test contract (REQUIRED)

Every `tests/<category>/test_*.py` file MUST expose:

```python
NAME = "stable_short_id"           # used by --only-tests filter
DESCRIPTION = "what is verified"   # shown in matrix.md

def run(client, model) -> dict:
    return {
        "ok": bool,                # pass/fail
        "info": {                  # surfaces in matrix.json
            "contract": "...",     # classifier reads this
            ...
        },
        "error": str | None,       # human-readable explanation if not ok
    }
```

`info.contract` strings — runner classifier rules
(`run_all.py:_classify`):
- contains `"reject"` → ⛔ REJECTED (contract)
- `"deprecation_signals"` key present → ⛔
- `"config_rejected_on_bedrock": True AND "header_accepted": True` → 🟡
- otherwise → 🟢 SUPPORTED

## Categories

| Subdirectory | What it verifies |
|---|---|
| `messages/` | Messages API basics: create, system, multi-turn, stop_sequences, max_tokens, metadata, service_tier, sampling deprecation, structured outputs |
| `streaming/` | SSE event schema, text deltas, tool_use deltas, thinking deltas, fine-grained tool streaming |
| `token_counting/` | `messages.count_tokens` rejection contract |
| `vision/` | base64 PNG, multi-image |
| `documents/` | PDF base64, PDF + citations |
| `citations/` | text document citations, search_result block |
| `tools/` | basic round trip, tool_choice, parallel, disable_parallel, tool_result+image, builtin tools (bash/memory/text_editor), strict tool use, token efficient |
| `thinking/` | adaptive, disabled, enabled-redirect contract, tools+thinking, interleaved beta |
| `caching/` | 5m cache, 1h cache, mixed buckets, multi-breakpoint, beta header rejection |
| `context/` | 1M context beta header |
| `multilingual/` | Korean, Japanese |
| `client/` | AsyncAnthropicBedrock equivalence |
| `unsupported/` | Anthropic-direct-only endpoints (Files / Batches / Models / server tools / computer use / tool search / compaction beta) |

## Rules

- **NEVER** re-implement `text_of` / `usage_breakdown` /
  `is_unsupported_tool_rejection`. Import from `tests._base`.
- **NEVER** redeclare `MODELS`, `REGION`, or `ALL_MODELS`. Import from
  `config`.
- **Cache tests** MUST embed `secrets.token_hex(8)` into the cached
  prefix. See ADR-001.
- **Strict assertions** — no OR-fallback that masks contract drift.
  Pin the specific signal you want (e.g. `create_1h > 0`).
- **Model-divergent contracts** are encoded with adaptive `info.contract`
  values, not separate test files. See
  `tests/messages/test_sampling_deprecated.py` for the pattern.
- **New test category** → add a `CLAUDE.md` to the new subdirectory and
  update the table above.
