# Anthropic docs vs measured Bedrock reality

A side-by-side comparison of every contract claim from the Anthropic public
documentation and what we actually observe when calling Bedrock from this
project's environment (account `***REDACTED-ACCOUNT***`, regions `ap-northeast-2`
and `us-east-1` / `us-west-2` for endpoint cross-checks; Opus 4.7, Opus 4.6,
Sonnet 4.6 unless noted).

Every row links to the test or probe script that produced the measurement.

## Scope of measurements

**All "measured" rows in this document refer to the existing
`bedrock-runtime` endpoint via the InvokeModel API (`/model/{id}/invoke`
or `.../invoke-with-response-stream`), called through the Anthropic
Python SDK.** The `bedrock-mantle` endpoint is intentionally not
exercised by this suite (see §"Configuration notes (Mantle out of scope)").
When this document says "Bedrock rejects X" or "Bedrock supports X", read
it as "Bedrock-runtime InvokeModel rejects/supports X from
`ap-northeast-2`" unless an explicit alternative is named.

## Conventions

- 🟢 **agree (supported)** — docs say supported, measurement confirms.
- ⛔ **agree (rejected)** — docs say not supported, measurement confirms rejection.
- 🟡 **docs nuance** — docs are not wrong but require interpretation; the
  layer / endpoint / model that actually gets the feature is narrower than
  the simple table cell suggests.
- ❗ **discrepancy** — docs and measurement genuinely differ.

---

## A. Real discrepancies (docs ≠ reality)

### A-1. ❗ 1-hour prompt cache TTL on Bedrock

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management table | `Prompt caching (1hr)` listed for `claudeApi`, `vertexAi`, `azureAiBeta`. **`bedrock` token absent.** |
| `code.claude.com/docs/en/amazon-bedrock` "Pin model versions" | `ENABLE_PROMPT_CACHING_1H=1` env var is documented for Claude Code on Bedrock. |
| Our measurement | `tests/caching/test_ttl_1h.py` + `results/variability_probe.json`: 5/5 cold-start trials populate `usage.cache_creation.ephemeral_1h_input_tokens` on Opus 4.7 in `ap-northeast-2`. Opus 4.6 and Sonnet 4.6 also pass. Mixed 5m+1h request tracks both buckets independently (`tests/caching/test_ttl_mixed.py`). |

The two docs pages internally contradict each other on whether 1h caching is
a Bedrock thing. The Bedrock-specific Claude Code docs document an
opt-in env var for it; the platform-wide overview table omits Bedrock from
the 1h row. Reality matches the env-var docs, not the overview table.

This means the overview table understates Bedrock support. A user reading
only the overview would conclude Bedrock is 5m-only; reality is 5m by
default + 1h via opt-in.

---

## B. Documentation nuance (real, but not contradiction)

### B-1. 🟡 Structured outputs on Opus 4.7 (Bedrock Invoke API)

| Source | Claim |
| --- | --- |
| `build-with-claude/structured-outputs` | "Amazon Bedrock: Generally available for Opus 4.6, Sonnet 4.6, Sonnet 4.5, Opus 4.5, Haiku 4.5. **Opus 4.7 ... available through Claude in Amazon Bedrock (the Messages-API Bedrock endpoint)**" — i.e. via Mantle. |
| Our measurement (Invoke API) | `tests/messages/test_structured_outputs.py` — Opus 4.6 / Sonnet 4.6 accept `output_config.format`, return schema-conformant JSON. Opus 4.7 returns `output_config.format: Extra inputs are not permitted`. |

Docs are technically correct on the standard Bedrock Invoke API path: the
feature is GA for Opus 4.6 / Sonnet 4.6 and not exposed for Opus 4.7
through Invoke. For Opus 4.7 the docs direct users to the Mantle endpoint
— **but the comparison doc shows Mantle is not deployed in `ap-northeast-2`**,
so users in this region currently have no working path for Opus 4.7 +
structured outputs even though it is "GA" globally. From any of the 13
Mantle regions (e.g. `us-east-1`, `ap-northeast-1` Tokyo) the docs path
should work; this suite does not measure that. See
[Configuration notes](#configuration-notes-mantle-out-of-scope).

### B-2. 🟡 Strict tool use (`tools[].strict=True`)

Same per-model pattern as B-1 on the Invoke API. `tests/tools/test_strict_tool_use.py`:

- 🟢 Opus 4.6 / Sonnet 4.6 on Invoke API — accepted, model produces
  schema-conformant tool input.
- ⛔ Opus 4.7 on Invoke API — rejected with
  `tools.0.custom.strict: Extra inputs are not permitted`.

### B-3. 🟡 Token counting on Bedrock — two APIs share the name

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management table | `Token counting` listed for `claudeApi bedrock vertexAi azureAiBeta`. |
| Anthropic SDK (`messages.count_tokens`) | Returns `"Token counting is not supported in Bedrock yet"` on every Bedrock model. (`tests/token_counting/test_count_tokens.py`) |
| AWS Bedrock-native `CountTokens` API | Reachable at `/model/{id}/count-tokens`. Probe (`scripts/probe_token_counting.py`) returns 403 with `User ... is not authorized to perform: bedrock:CountTokens`, which proves the route exists — IAM permission gates it, not lack of feature. |

The docs row "supported on Bedrock" refers to the AWS-native `CountTokens`
API, which is independent of the Anthropic SDK's `count_tokens()` method.
Two different APIs share the same name. The SDK-layer rejection is not a
docs error; it is a layer-level gap that is going to close (the SDK message
literally says "yet").

### Configuration notes (Mantle out of scope)

This verification suite explicitly does **not** measure the Mantle
endpoint contract. We surface enough configuration information here that
a reader who *does* want to use Mantle has the right hostname, regional
availability, and access prerequisites.

The authoritative internal reference for Bedrock endpoint shapes is
[`docs/bedrock-api-endpoints-comparison.md`](../docs/bedrock-api-endpoints-comparison.md),
which catalogs all three endpoints (`bedrock` control plane, `bedrock-runtime`
inference, `bedrock-mantle` inference) and the five API patterns Bedrock
exposes (Responses, Chat Completions, Messages, Converse, InvokeModel).
The summary below is sufficient for understanding why this suite skips
Mantle; consult that doc for full coverage.

**Hostname differences** (different domain suffix AND subdomain):

```
Invoke API: bedrock-runtime.{region}.amazonaws.com
Mantle:     bedrock-mantle.{region}.api.aws
```

Earlier passes of this project hit `bedrock-runtime.../v1/messages` and
got `UnknownOperationException`. That was a *wrong-host* artifact — the
`/v1/messages` path lives on the Mantle host, not the Invoke host. Once
the correct Mantle host is used, the previously-observed
`UnknownOperationException` would resolve into one of: a real response,
an IAM auth failure, an allowlist rejection, or a region-not-deployed
error — depending on environment.

**Mantle region availability** (per the internal comparison doc, 13 regions
as of 2026-05-03):

```
us-east-1, us-east-2, us-west-2,
ap-northeast-1 (Tokyo), ap-south-1 (Mumbai),
ap-southeast-2 (Sydney), ap-southeast-3 (Jakarta),
eu-central-1 (Frankfurt), eu-west-1, eu-west-2,
eu-south-1, eu-north-1,
sa-east-1
```

**`ap-northeast-2` (Seoul) is NOT in this list.** This project runs
in Seoul, so Mantle is not even reachable in this environment — not an
allowlist issue, just regional non-deployment. Opus 4.7 + structured
outputs has no working Bedrock path *from this region* until Mantle
ships in Seoul.

**Model gating on Mantle** (asymmetric):
- Both endpoints: Claude Haiku 4.5, Claude Opus 4.7, Mythos Preview
  (Mantle-only for Mythos), and many third-party models (DeepSeek,
  Gemma, Mistral, Qwen, etc.).
- `bedrock-runtime` only: Claude Opus 4.1 / 4.5 / 4.6, Claude
  Sonnet 4 / 4.5 / 4.6, all Amazon Nova/Titan, Cohere, Llama, embedding
  models, image-generation models. These cannot run on Mantle even where
  Mantle is deployed.

This is why our test results made sense: Opus 4.6 / Sonnet 4.6 work for
structured outputs on `bedrock-runtime` (their only available endpoint),
and Opus 4.7 rejects on `bedrock-runtime` (it expects Mantle for that
feature).

**Authentication** for Mantle: Bedrock API Key (Bearer) *or* AWS
credentials with SigV4. `bedrock-runtime` only accepts AWS credentials;
the Bedrock API Key works on Mantle but not on the Invoke API for
streaming `/model/{id}/invoke-with-response-stream` paths in some
configurations — verify per environment.

**Claude Code env vars** to use Mantle:
- `CLAUDE_CODE_USE_MANTLE=1` — selects Mantle.
- `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` — override the host (useful when a
  gateway sits in front of Mantle, or when forcing a region whose Mantle
  endpoint differs from `AWS_REGION`).

Adding Mantle to this verification suite is out of scope for the current
pass. If a future pass picks it up, start from
`bedrock-mantle.{region}.api.aws` in one of the 13 regions above — not
from `bedrock-runtime`, and not from `ap-northeast-2`.

---

## C. Spurious discrepancies (caused by our test bugs, now fixed)

These were claimed as docs vs reality conflicts in earlier passes of this
project. Investigation showed our test code was sending the wrong shape.
After correcting the test, docs and reality agree.

### C-1. ✅ Structured outputs "rejected on Bedrock"

- Old test (`tests/unsupported/test_structured_outputs_response_format_rejected.py`,
  removed) sent `response_format` (an OpenAI-style field name).
  Anthropic's API does not have that field, so the rejection
  `"response_format: Extra inputs are not permitted"` was an unknown-field
  error, not a feature-rejection.
- New test (`tests/messages/test_structured_outputs.py`) uses
  `output_config.format` (current Anthropic GA parameter). Now confirms
  the real per-model contract — see B-1.

### C-2. ✅ Strict tool use "rejected on Bedrock"

- Old test pinned blanket rejection on Bedrock, but the actual API
  accepted `strict=True` on Opus 4.6 and Sonnet 4.6. Result: ❌ on those
  models in older matrix runs, because the test was asserting the wrong
  contract. The Opus 4.7 rejection it captured was real, but the test
  generalized incorrectly.
- New test (`tests/tools/test_strict_tool_use.py`) is per-model adaptive.
  See B-2.

---

## D. Aligned (no discrepancy)

For completeness, the documentation feature table accurately predicts
behavior for the rest of the surfaces this project measures:

- **Prompt caching (5m)** — supported on Bedrock per docs and per
  `tests/caching/test_on_messages.py` etc.
- **Multi-breakpoint cache** — supported per `tests/caching/test_multi_breakpoint.py`.
- **`extended-cache-ttl-2025-04-11` beta header** — Anthropic-only per
  conventional reading; Bedrock returns "invalid beta flag"
  (`tests/caching/test_extended_ttl_header_rejected.py`).
- **Server-side tools** (web search / code execution / web fetch / memory
  server tool / MCP connector / Files API / Batches / Computer use) —
  docs list these as Anthropic-API-direct or claudeApiBeta, and our
  `tests/unsupported/` directory confirms the rejection on Bedrock.
- **Streaming**, **PDF**, **citations**, **vision**, **multi-turn**,
  **1M context**, **adaptive thinking**, **interleaved thinking** — all
  match docs.
- **Bash / memory / text editor client-side tools** — match docs.

---

## E. Opus 4.7 specific contract changes (docs do call these out, but the
"feature available" tables can mislead)

The general feature table does not split rows by model. These contract
changes apply specifically to Opus 4.7 and would surprise a reader who
assumed all Bedrock-listed features just work:

| Surface | Docs note exists? | Our test |
| --- | --- | --- |
| Sampling parameters (`temperature` / `top_p` / `top_k`) deprecated → 400 | Implicit (release notes) | `tests/messages/test_sampling_deprecated.py` |
| `thinking.type=enabled` rejected; use `adaptive` + `output_config.effort` | Docs flag adaptive as "recommended thinking mode for Opus 4.7" | `tests/thinking/test_enabled_with_effort.py` |
| Assistant prefill (trailing assistant message) rejected — "must end with a user message" | Not prominently flagged | `tests/messages/test_assistant_prefill.py` |
| `output_config.format` rejected on Invoke API | Implicit (Mantle requirement note in structured-outputs page) | `tests/messages/test_structured_outputs.py` |
| `tools[].strict=true` rejected on Invoke API | Same | `tests/tools/test_strict_tool_use.py` |
| Computer use (`computer-use-2025-01-24` tool spec) rejected | Docs say `bedrockBeta` for computer use generally; Opus 4.7-specific status is empirical | `tests/unsupported/test_computer_use_rejected.py` |
| Tool search (`tool-search-tool-2025-09-25`) rejected | Same shape as computer use | `tests/unsupported/test_tool_search_rejected.py` |

These all track the broader theme: Opus 4.7 has narrower contract surface
than older Bedrock models within the same Bedrock cell of the docs table.

---

## F. Reproducing each row

```bash
# Caching contract (incl. 1h finding A-1)
python run_all.py --all-models --only caching

# Structured outputs (B-1, C-1)
python run_all.py --all-models --only-tests structured_outputs
python scripts/probe_structured_outputs.py

# Strict tool use (B-2, C-2)
python run_all.py --all-models --only-tests strict_tool_use

# Token counting (B-3)
python run_all.py --only-tests count_tokens
python scripts/probe_token_counting.py

# Mantle endpoint — out of scope for this suite. See "Configuration notes
# (Mantle out of scope)" above for the correct host
# (bedrock-mantle.{region}.api.aws) and access prerequisites.

# Claude Code wire-level capture (cross-references this matrix)
python scripts/intercept_proxy.py &
ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001 \
  CLAUDE_CODE_USE_BEDROCK=1 claude -p "..."
```

All measurements reproducible with `AWS_BEARER_TOKEN_BEDROCK` set.

---

## G. Last reviewed

- 2026-05-03 — initial cross-walk between docs and matrix.
- All inline numbers above were re-verified against `results/matrix.json`
  on the date stamped at the top of `results/latest.md`.
