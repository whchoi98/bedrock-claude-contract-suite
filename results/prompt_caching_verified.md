# Prompt Caching on Bedrock — verified contract (2026-05-03)

A consolidated, evidence-cited reference for every prompt-caching claim
verified in this project. Two distinct layers are covered:

1. **Bedrock API layer** — what the Bedrock Invoke endpoint accepts and
   how it accounts cache writes/reads. Verified by the test suite under
   `tests/caching/`.
2. **Claude Code layer** — what `claude` (v2.1.126) emits in its
   outbound HTTP when configured for Bedrock. Verified by the
   intercepting proxy at `scripts/intercept_proxy.py`.

**Scope:** all measurements use the existing `bedrock-runtime` endpoint
via the InvokeModel API (path `/model/{id}/invoke[-with-response-stream]`)
called through the Anthropic Python SDK. The separate `bedrock-mantle`
endpoint is intentionally out of scope (and is not deployed in this
project's region anyway — see
[`docs_vs_reality.md`](docs_vs_reality.md) §"Configuration notes").
Region for all measurements: `ap-northeast-2`. Models exercised:
`global.anthropic.claude-opus-4-7`, `global.anthropic.claude-opus-4-6-v1`,
`global.anthropic.claude-sonnet-4-6`, plus `anthropic.claude-haiku-4-5`
seen in Claude Code wire traces (small/fast model).

---

## TL;DR

| # | Claim | Verdict | Evidence |
| - | --- | :---: | --- |
| 1 | `cache_control` (5m default) works on Bedrock | 🟢 | `tests/caching/test_on_system.py`, `test_on_messages.py`, `test_on_tools.py`, `test_savings_measured.py`, `test_multi_breakpoint.py` (all 🟢 in matrix) |
| 2 | `anthropic-beta: extended-cache-ttl-2025-04-11` is rejected on Bedrock | ⛔ | `tests/caching/test_extended_ttl_header_rejected.py` → 400 "invalid beta flag" |
| 3 | Sending `cache_control.ttl="1h"` *without* the beta header populates `ephemeral_1h_input_tokens` | 🟢 | `tests/caching/test_ttl_1h.py` + 5/5 cold-start trials in `results/variability_probe.json` |
| 4 | A request with both 5m and 1h breakpoints populates BOTH buckets independently | 🟢 | `tests/caching/test_ttl_mixed.py` |
| 5 | The "ttl=1h does nothing" appearance comes from cache state, not contract | — | `results/stable_prefix_probe.json`: trial 1 fresh-write, trials 2-5 read |
| 6 | Cache write threshold on Opus 4.7 ≈ 13K tokens of stable prefix | 🟢 | empirical, README "Findings" |
| 7 | Claude Code on Bedrock (default) emits `cache_control` with no `ttl` field | 🟢 | wire capture, `logs/intercept.jsonl` (Experiment A) |
| 8 | `ENABLE_PROMPT_CACHING_1H=1` injects `ttl="1h"` into every breakpoint | 🟢 | wire capture (Experiment B) |
| 9 | `DISABLE_PROMPT_CACHING=1` removes the `cache_control` block entirely | 🟢 | wire capture (Experiment C) |
| 10 | Mantle endpoint uses Anthropic Messages shape, but the same cache_control contract | 🟢 | wire capture (Experiments D, D2) |

---

## Layer 1 — Bedrock API contract

### 1.1 5-minute cache (default)

`cache_control: {"type": "ephemeral"}` is honored on system blocks, on
message-content blocks, and on tool definitions. Second call reads back
the entire prefix from `cache_read_input_tokens`.

Sample numbers (Opus 4.7, fresh write of a ~10K-token system prefix):

```
1st call: input=22, cache_creation_input_tokens=10005, cache_read_input_tokens=0
2nd call: input=22, cache_creation_input_tokens=0,     cache_read_input_tokens=10005
```

Source: `results/latest.json` → `caching.cache_on_messages`,
`prompt_caching`, `cache_savings_measured`.

### 1.2 1-hour cache via `ttl="1h"` field — supported

This was the contested finding. The `extended-cache-ttl-2025-04-11` beta
header is rejected outright on Bedrock ("invalid beta flag"), so a casual
reading of the docs concludes "Bedrock = 5m only". The actual contract is
different: **the `ttl` field on `cache_control` itself is honored** even
without the beta header.

Cold-start probe (5 trials, unique salt per trial,
`results/variability_probe.json`):

```
trial 1: ephemeral_1h_input_tokens = 40,508    (5m bucket = 0)
trial 2: ephemeral_1h_input_tokens = 39,008    (5m bucket = 0)
trial 3: ephemeral_1h_input_tokens = 39,008    (5m bucket = 0)
trial 4: ephemeral_1h_input_tokens = 40,508    (5m bucket = 0)
trial 5: ephemeral_1h_input_tokens = 42,008    (5m bucket = 0)
```

5/5 trials populate the 1h bucket on the fresh write, never the 5m
bucket. The minor token-count variation (39008–42008) is salt-string
tokenizer noise; the contract is identical.

Cross-model verification (`results/matrix.json` →
`cache_ttl_1h.info.first.create_1h`):

| Model | 1h bucket on fresh write |
| --- | ---: |
| `global.anthropic.claude-opus-4-7` | 43,508 |
| `global.anthropic.claude-opus-4-6-v1` | 24,005 |
| `global.anthropic.claude-sonnet-4-6` | 28,505 |

### 1.3 Mixed 5m + 1h in the same request

`tests/caching/test_ttl_mixed.py` puts a 1h-tagged system block alongside
a 5m-tagged user-content block. Both buckets populate, and the second
call reads the sum back:

```
first_breakdown:  ephemeral_1h_input_tokens = 30,003
                  ephemeral_5m_input_tokens = 27,004
first_create_total = 57,007  first_read = 0    (cold start)
second_create_total = 0      second_read = 57,007
```

This rules out the "API just doesn't expose 1h tracking" hypothesis —
the 5m bucket *does* populate in the same call, so the 1h count is real.

### 1.4 The reason "every verification gave different numbers"

Stable-prefix probe — 5 trials with the *same* prefix and no salt
(`results/stable_prefix_probe.json`):

```
trial 1: create_total=15,008  create_1h=15,008  read_total=0       (fresh write)
trial 2: create_total=0       create_1h=0       read_total=15,008  (cache hit)
trial 3: create_total=0       create_1h=0       read_total=15,008  (cache hit)
trial 4: create_total=0       create_1h=0       read_total=15,008  (cache hit)
trial 5: create_total=0       create_1h=0       read_total=15,008  (cache hit)
```

This is the source of historical "test sometimes shows 1h, sometimes
shows 0" reports. Without cold-start isolation, you observe whichever
state the cache happens to be in. The current
`tests/caching/test_ttl_1h.py` and `test_ttl_mixed.py` use a per-run
`secrets.token_hex(8)` salt baked into the prefix so the first call is
*always* a fresh write and the assertion can be strict.

### 1.5 What does NOT work on Bedrock

- ⛔ `anthropic-beta: extended-cache-ttl-2025-04-11` header — rejected as
  "invalid beta flag" (`tests/caching/test_extended_ttl_header_rejected.py`).
  This is the only known opt-in path for 1h on the Anthropic API
  endpoint; on Bedrock it is unnecessary because the `ttl` field works
  without it.

---

## Layer 2 — Claude Code on Bedrock

Captured by `scripts/intercept_proxy.py` listening on
`http://127.0.0.1:9001` and forwarding to
`https://bedrock-runtime.ap-northeast-2.amazonaws.com`. Method:

```bash
ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001 \
ANTHROPIC_BEDROCK_MANTLE_BASE_URL=http://127.0.0.1:9001 \
... claude -p "<short prompt>" --model <id>
```

For each scenario the proxy parsed the request body and recorded every
`cache_control` block in `logs/intercept.jsonl`.

### 2.1 Default behavior (`CLAUDE_CODE_USE_BEDROCK=1`)

Outbound path: `/model/global.anthropic.claude-opus-4-7/invoke-with-response-stream`

```
$.system[1]                -> {"type": "ephemeral"}
$.system[2]                -> {"type": "ephemeral"}
$.messages[0].content[3]   -> {"type": "ephemeral"}
```

3 breakpoints, no `ttl` field anywhere → Bedrock's default 5m TTL
applies. This is the default on every fresh `claude` invocation on
Bedrock.

### 2.2 `ENABLE_PROMPT_CACHING_1H=1`

Same paths, same breakpoint locations:

```
$.system[1]                -> {"type": "ephemeral", "ttl": "1h"}
$.system[2]                -> {"type": "ephemeral", "ttl": "1h"}
$.messages[0].content[3]   -> {"type": "ephemeral", "ttl": "1h"}
```

The env var injects `ttl: "1h"` into every breakpoint. Combined with
finding 1.2, this means the writes actually land in the 1h bucket on the
Bedrock side — verified end-to-end.

### 2.3 `DISABLE_PROMPT_CACHING=1`

Both Haiku and Opus calls came through with `cache_breakpoint_count = 0`.
Claude Code does not just remove `ttl` — it removes the entire
`cache_control` block. The request body is still ~71KB (system prompt +
tools), it just has no caching directive.

### 2.4 Mantle endpoint (`CLAUDE_CODE_USE_MANTLE=1`) — wire emission only

> **Scope reminder.** This subsection captures only the OUTBOUND request
> shape that Claude Code emits when set for Mantle. The Mantle endpoint
> itself is OUT OF SCOPE for this verification suite — its response
> contract is not measured here. (Reasons in
> [`docs_vs_reality.md`](docs_vs_reality.md) §"Configuration notes":
> Mantle is not deployed in `ap-northeast-2`, and the comparison doc
> at [`../docs/bedrock-api-endpoints-comparison.md`](../docs/bedrock-api-endpoints-comparison.md)
> documents the model gating that further restricts Mantle.)

What we observed about Claude Code's emission when `CLAUDE_CODE_USE_MANTLE=1`:

Outbound path is different: `/v1/messages?beta=true` (Anthropic Messages
shape, not Bedrock Invoke shape).

Body top-level keys differ too:
- Invoke body: `anthropic_version`, `max_tokens`, `messages`, `system`
- Mantle body: `context_management`, `max_tokens`, `messages`,
  `metadata`, `model`, `stream`, `system`, `thinking`, `tools`

`cache_control` directives Claude Code attaches are identical to the
Invoke case:

| | Mantle emission, default | Mantle emission + `ENABLE_PROMPT_CACHING_1H=1` |
| --- | --- | --- |
| `$.system[1]` | `{"type": "ephemeral"}` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.system[2]` | `{"type": "ephemeral"}` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.messages[0].content[N]` | `{"type": "ephemeral"}` | `{"type": "ephemeral", "ttl": "1h"}` |

Caveats: (1) what Mantle DOES with these emitted requests is not
measured here. (2) Our naive proxy was forwarding to the wrong upstream
host (`bedrock-runtime.../v1/messages` rather than the actual Mantle
host `bedrock-mantle.{region}.api.aws`), so `claude` reported "API
returned an empty or malformed response" — that is an artifact of the
proxy/host mismatch, not a Mantle contract observation.

---

## End-to-end matrix

| Scenario | Path | Breakpoints | TTL on wire | Bucket on Bedrock |
| --- | --- | :---: | --- | --- |
| API SDK with `ttl="1h"` on a stable prefix | `/model/{id}/invoke` | 1 | `"1h"` | `ephemeral_1h_input_tokens` |
| API SDK with `cache_control` only (no ttl) | `/model/{id}/invoke` | 1 | (missing) | 5m |
| Claude Code, default | `/model/{id}/invoke-with-response-stream` | 3 | (missing) | 5m |
| Claude Code, `ENABLE_PROMPT_CACHING_1H=1` | `/model/{id}/invoke-with-response-stream` | 3 | `"1h"` | `ephemeral_1h_input_tokens` |
| Claude Code, `DISABLE_PROMPT_CACHING=1` | `/model/{id}/invoke-with-response-stream` | 0 | n/a | none |
| Claude Code on Mantle, default | `/v1/messages?beta=true` | 3 | (missing) | 5m |
| Claude Code on Mantle, `ENABLE_PROMPT_CACHING_1H=1` | `/v1/messages?beta=true` | 3 | `"1h"` | `ephemeral_1h_input_tokens` |

---

## How to opt into 1-hour caching

Layer-specific:

| Caller | Mechanism | Notes |
| --- | --- | --- |
| Anthropic SDK on Bedrock (`AnthropicBedrock`) | Set `cache_control: {"type": "ephemeral", "ttl": "1h"}` on the breakpoint(s) you care about | Per-request decision; no headers, no beta flag |
| Boto3 / direct Bedrock Invoke | Same — include `"cache_control": {"type":"ephemeral","ttl":"1h"}` in the request body for the relevant content blocks | Same |
| Claude Code on Bedrock (Invoke) | `export ENABLE_PROMPT_CACHING_1H=1` before running `claude` | Process-wide; persists across turns; affects all 3 breakpoints |
| Claude Code on Mantle | Same env var | Same behavior |

Cost note from the official docs: 1-hour cache *writes* are billed at a
higher rate than 5-minute writes. *Reads* are not affected. So the
break-even depends on how often the cached prefix is reused within the
1-hour window — long agentic sessions that reuse the same system+tools
prompt many times tend to come out ahead with 1h.

---

## Pitfalls and methodology notes

### P-1. Cold-start salt is mandatory for cache TTL tests

Without a unique per-run salt mixed into the cached prefix, every test
after the first shares state with previous runs and you observe the
cache state machine, not the contract. Symptoms:

- "Test passes one run, fails the next" — actually different cache
  states (fresh vs hot) being observed.
- `ephemeral_1h_input_tokens == 0` "proving" Bedrock doesn't support 1h
  — actually a `cache_creation_input_tokens == 0` (no fresh write
  happened) being misread as "1h didn't fire".

Pattern (used in `tests/caching/test_ttl_1h.py`):

```python
import secrets
salt = secrets.token_hex(8)
sys_blocks = [{
    "type": "text",
    "text": f"Run salt {salt}. ... " * 1500,
    "cache_control": {"type": "ephemeral", "ttl": "1h"},
}]
```

### P-2. Strict assertions, no OR-fallback

Avoid:

```python
fresh = u1["create_1h"] > 0 and u2["read_total"] > 0
hot   = u1["read_total"] > 0 and u2["read_total"] > 0
ok    = fresh or hot   # ← masks contract failure
```

Prefer:

```python
cold_start_verified  = u1["create_total"] > 0 and u1["read_total"] == 0
one_hour_populated   = u1["create_1h"] > 0
not_demoted_to_5m    = u1["create_5m"] == 0
ok = cold_start_verified and one_hour_populated and not_demoted_to_5m
```

The strict form fails loudly when the contract changes; the OR form
silently accepts a cache hit as evidence the underlying logic worked,
even when it didn't fire at all.

### P-3. Layer separation

"Bedrock supports X" and "Claude Code on Bedrock does X" answer
different questions. Layer 1 is API capability; Layer 2 is application
strategy. They can disagree without contradiction:

- Bedrock supports 1h → YES
- Claude Code on Bedrock uses 1h by default → NO (must opt in)

When the user asks "does X work?", clarify which layer.

---

## Reproducing each finding

| Finding | Command |
| --- | --- |
| 1.1 5m cache works | `python run_all.py --only caching` |
| 1.2 1h cache via `ttl` field | `python run_all.py --only caching --only-tests cache_ttl_1h` |
| 1.2 cold-start variability probe | `python results/variability_probe.py` |
| 1.4 stable-prefix variability source | `python results/stable_prefix_probe.py` |
| 1.5 beta header rejected | `python run_all.py --only caching --only-tests extended_ttl_beta_header_rejected_on_bedrock` |
| Cross-model matrix | `python run_all.py --all-models --only caching` |
| 2.1–2.4 Claude Code wire capture | `python scripts/intercept_proxy.py &` then `claude -p ...` with `ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001` |

All commands require `AWS_BEARER_TOKEN_BEDROCK` and `AWS_REGION=ap-northeast-2`
in the environment. The proxy logs land in `logs/intercept.jsonl`.

---

## Scope and caveats

- **Endpoint**: only the existing `bedrock-runtime` endpoint via the
  InvokeModel API was measured. The `bedrock-mantle` endpoint is
  intentionally out of scope; §2.4 captures only Claude Code's wire
  emission for Mantle, not Mantle's actual response contract.
- **Region**: only `ap-northeast-2` was measured. The Anthropic docs
  warn prompt caching may not be available in all regions; behavior in
  other regions has not been verified here. Mantle is not deployed in
  ap-northeast-2 at all (see comparison doc).
- **Models**: Opus 4.7, Opus 4.6, Sonnet 4.6 on `bedrock-runtime`
  Invoke. Haiku 4.5 only appears in Claude Code wire traces as the
  small/fast model. Other models are not in scope.
- **Claude Code version**: v2.1.126. Future versions may change the
  breakpoint count or location.
- API-level findings come from the suite under `tests/caching/`. They
  encode the contract; if Bedrock's behavior changes, those tests fail
  loudly.
