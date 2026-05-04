# Onboarding

Quickstart for a new contributor to `bedrock-claude-contract-suite`.

## Prerequisites

- Python 3.9 or later (`python3 --version`)
- `anthropic` SDK installed (`python3 -c "import anthropic"`)
- `httpx` and `boto3` for probe scripts
- An Amazon Bedrock account with access to:
  - `global.anthropic.claude-opus-4-7`
  - `global.anthropic.claude-opus-4-6-v1`
  - `global.anthropic.claude-sonnet-4-6`
- Access enabled in the `ap-northeast-2` (Seoul) region
- A Bedrock API Key (`AWS_BEARER_TOKEN_BEDROCK`) issued to your AWS
  account. The Bedrock console "API keys" page generates these.

## Setup

```bash
# 1. Install dependencies
pip install anthropic httpx boto3

# 2. Configure credentials
cp .env.example .env
# Edit .env — set AWS_BEARER_TOKEN_BEDROCK
source .env

# 3. Smoke test (single test, ~$0.05)
python3 run_all.py --only-tests basic
```

## First full run

Read the cost notice in `verify.sh` first — a full matrix run is
approximately **$5 USD** (3 models × ~57 tests × ~176 API calls).

```bash
# Interactive launcher with cost confirmation
./verify.sh

# Or direct
python3 run_all.py --all-models
```

Result locations:
- `results/latest.{json,md}` — single-model run
- `results/matrix.{json,md}` — multi-model matrix
- Token-usage summary printed at the end of every run

## Project structure (high level)

| Path | Purpose |
|---|---|
| `config.py` | model IDs, region, beta-header constants |
| `client.py` | `make_client()` factory |
| `run_all.py` | discover + execute + classify + token track |
| `verify.sh` | interactive launcher with cost notice |
| `tests/_base.py` | shared harness primitives |
| `tests/<cat>/test_*.py` | individual contract tests |
| `scripts/probe_*.py` | ad-hoc API contract probes |
| `scripts/intercept_proxy.py` | captures Claude Code outbound HTTP |
| `results/` | matrix output + verified findings docs |
| `docs/` | architecture, ADRs, runbooks, endpoint comparison |

See `docs/architecture.md` for the full diagram and component
descriptions.

## Reading list

Before contributing, skim:

1. **Root `CLAUDE.md`** — conventions, commands, sync rules.
2. **`results/prompt_caching_verified.md`** — the canonical caching
   contract reference.
3. **`results/docs_vs_reality.md`** — Anthropic docs vs measured Bedrock
   contract.
4. **`docs/bedrock-api-endpoints-comparison.md`** — Bedrock endpoint
   landscape (3 endpoints × 5 API patterns).
5. **`docs/decisions/ADR-001-cold-start-salt-for-cache-tests.md`** —
   why every cache test embeds a salt; the most load-bearing convention
   in this codebase.

## Contributing a new test

1. Pick a category under `tests/`. If none fits, create a new directory
   AND a `tests/<cat>/CLAUDE.md` describing the role.
2. Create `tests/<cat>/test_<name>.py` exposing:
   ```python
   NAME = "stable_id"
   DESCRIPTION = "short description of what's verified"
   def run(client, model) -> dict:
       return {"ok": bool, "info": {"contract": "...", ...}, "error": None}
   ```
3. If the test divides cleanly into "supported" vs "rejected" branches
   per model, follow the model-divergent pattern in
   `tests/messages/test_sampling_deprecated.py`.
4. If it touches caching, embed a `secrets.token_hex(8)` salt — see
   ADR-001.
5. Reuse `tests._base` helpers — `text_of`, `usage_breakdown`,
   `is_unsupported_tool_rejection`. Don't re-implement.
6. Run a single-test smoke: `python3 run_all.py --only-tests <name>`.
7. Run the full matrix to confirm contract per model.
8. If a finding requires permanent reference, add a row to
   `results/docs_vs_reality.md` with claim → evidence linkage.

## Common pitfalls

- **Cache test without salt** → run-to-run variance. See ADR-001.
- **OR-fallback assertion** (`fresh_path or hot_path`) → silently masks
  contract drift. Use strict single-condition assertions.
- **Hardcoded model list / region in a probe** → import from
  `config.ALL_MODELS` and `config.REGION`.
- **`response_format` instead of `output_config.format`** →
  `response_format` is OpenAI naming; Anthropic uses
  `output_config.format`. Sending the wrong field name produces a
  "Extra inputs not permitted" error that looks like rejection but is
  actually just an unknown field.

## Getting help

- For Bedrock-side questions: see
  `docs/bedrock-api-endpoints-comparison.md` for endpoint shapes.
- For test patterns: check existing tests in the same category.
- For docs vs reality questions: `results/docs_vs_reality.md`.
