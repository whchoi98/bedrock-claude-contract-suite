# Project Context

## Overview

`bedrock-claude-contract-suite` — a categorized verification suite for Amazon Bedrock's
hosted Anthropic Claude API. The suite encodes the runtime contract of each
feature surface (caching, tools, thinking, vision, etc.) as a deterministic
test that returns 🟢 supported / ⛔ rejected / 🟡 mixed / ❌ fail. Mirrors
the categories of Anthropic's Build with Claude documentation so behavior
gaps between docs and reality are visible per-test.

Primary deliverable: `results/matrix.{json,md}` and `results/latest.{json,md}`
showing per-model, per-test contract status.

## Tech Stack

- **Language**: Python 3.9+
- **SDK**: `anthropic` (`AnthropicBedrock` client; `extra_body` / `extra_headers`
  for new-model fields not yet in the typed schema)
- **HTTP utilities**: `httpx` (probes), `boto3` (SigV4 in selected probes)
- **Auth**: AWS Bedrock API Key via `AWS_BEARER_TOKEN_BEDROCK` (Bearer)
- **No build system**: tests are plain `python3` modules, no packaging

## Project Structure

```
config.py                    # MODEL_ID, REGION, ALL_MODELS, beta-header constants
client.py                    # make_client() factory (reads AWS_BEARER_TOKEN_BEDROCK)
run_all.py                   # discovers tests/<cat>/test_*.py, runs them, prints
                             #   per-category + token-usage summary
verify.sh                    # interactive launcher with cost/token notice

tests/                       # contract suite
  _base.py                   #   Result, execute(), text_of(),
                             #   usage_breakdown(), is_unsupported_tool_rejection()
  <category>/test_*.py       #   each exposes NAME, DESCRIPTION, run(client, model)

scripts/                     # one-off probes and the intercept proxy
  intercept_proxy.py         #   captures Claude Code outbound HTTP for analysis
  probe_*.py                 #   ad-hoc API contract probes

results/                     # generated artifacts + verified findings
  latest.{json,md}           #   single-model run output
  matrix.{json,md}           #   3-model matrix output
  *_probe.json               #   raw probe captures
  prompt_caching_verified.md #   curated caching contract reference
  docs_vs_reality.md         #   docs vs measured contract diff

docs/                        # operational and architecture documentation
  bedrock-api-endpoints-comparison.md  # canonical 5-API breakdown
  architecture.md            #   system architecture (KR/EN)
  decisions/                 #   ADRs
  runbooks/                  #   operational runbooks

fixtures/                    # binary inputs (red_4x4.png, sample.pdf)
logs/                        # intercept_proxy capture output
.claude/                     # hooks, skills, commands, agents
tools/prompts/               # prompt assets
```

## Conventions

- **Test contract**: each `tests/<cat>/test_*.py` MUST expose
  `NAME: str`, `DESCRIPTION: str`, and
  `run(client, model) -> {"ok": bool, "info": dict, "error": str|None}`.
  See `tests/_base.py` for `Result` dataclass and `execute()`.
- **Contract classification**: the runner reads `info.contract` — if it
  contains `"reject"` it's marked ⛔; otherwise 🟢. `🟡` requires both
  `config_rejected_on_bedrock=True` and `header_accepted=True`.
- **Cold-start salt**: any cache-related test MUST embed
  `secrets.token_hex(8)` into the cached prefix to force a fresh write.
  Stable prefixes share state across invocations and produce false
  positives. See `results/prompt_caching_verified.md` §P-1.
- **Strict assertions, no OR-fallback**: avoid `fresh_path or hot_path`
  — it silently masks contract changes. Pin the specific signal you
  want to observe (`create_total > 0`, `create_1h > 0`, etc.).
- **Model-divergent contracts**: when behavior differs by model, encode
  both branches in the same test using `info.contract` (e.g.
  `"rejected_deprecated"` vs `"supported_legacy"`). See
  `tests/messages/test_sampling_deprecated.py` for the pattern.
- **Endpoint scope**: tests target `bedrock-runtime` Invoke API only.
  Mantle (`bedrock-mantle.{region}.api.aws`) is out of scope; see
  `results/docs_vs_reality.md` §"Configuration notes".

## Key Commands

```bash
# Single-model run (uses config.MODEL_ID)
python3 run_all.py
python3 run_all.py --only caching tools
python3 run_all.py --only-tests cache_ttl_1h

# 3-model matrix (writes results/matrix.{json,md})
python3 run_all.py --all-models

# Interactive launcher (with cost/token notice)
./verify.sh
./verify.sh all
./verify.sh matrix
./verify.sh -h

# Probes (write results/*_probe.json)
python3 scripts/probe_structured_outputs.py
python3 scripts/probe_token_counting.py
python3 results/variability_probe.py
python3 results/stable_prefix_probe.py
```

Required env: `AWS_BEARER_TOKEN_BEDROCK`. Optional: `AWS_REGION`
(default `ap-northeast-2`), `BEDROCK_MODEL_ID`.

---

## Auto-Sync Rules

Rules below are applied automatically after Plan mode exit and on major code changes.

### Post-Plan Mode Actions

After exiting Plan mode (`/plan`), before starting implementation:

1. **Architecture decision made** → Update `docs/architecture.md`
2. **Technical choice / trade-off made** → Create `docs/decisions/ADR-NNN-title.md`
3. **New test category added under `tests/`** → Create `CLAUDE.md` in that
   directory; update README test inventory
4. **Operational procedure defined** → Create runbook in `docs/runbooks/`
5. **Verified finding requires permanent reference** → Add to
   `results/prompt_caching_verified.md` or `results/docs_vs_reality.md`
6. **Changes needed in this file** → Update relevant sections above

### Code Change Sync Rules

- New directory under `tests/` → Must create `CLAUDE.md` alongside
- New test file → Must follow `NAME` / `DESCRIPTION` / `run()` contract
- New shared helper → Lift into `tests/_base.py`, not duplicated per file
- Cache-related test → Must use cold-start salt (see Conventions §3)
- New env var → Update `verify.sh` token notice and `.env.example`
- New API contract finding → Update `results/docs_vs_reality.md` row
- Infrastructure / endpoint shape changed → Update
  `docs/bedrock-api-endpoints-comparison.md`

### ADR Numbering

Find the highest number in `docs/decisions/ADR-*.md` and increment by 1.
Format: `ADR-NNN-concise-title.md`.
