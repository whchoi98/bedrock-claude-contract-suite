# Anthropic docs vs measured Bedrock reality

[![Last reviewed](https://img.shields.io/badge/last%20reviewed-2026--05--04-green.svg)](#g-last-reviewed)
[![Real discrepancies](https://img.shields.io/badge/❗%20real%20discrepancies-4-red.svg)](#a-real-discrepancies-docs--reality)
[![Doc nuance](https://img.shields.io/badge/🟡%20doc%20nuance-3-yellow.svg)](#b-documentation-nuance-real-but-not-contradiction)
[![Endpoint](https://img.shields.io/badge/endpoint-bedrock--runtime%20Invoke%20API-blue.svg)](#scope-of-measurements)
[![English](https://img.shields.io/badge/lang-English-blue.svg)](#english)
[![한국어](https://img.shields.io/badge/lang-한국어-red.svg)](#한국어)

A side-by-side comparison of every contract claim from the Anthropic public
documentation and what we actually observe when calling Bedrock from this
project's environment (regions `ap-northeast-2` and `us-east-1` /
`us-west-2` for endpoint cross-checks; Opus 4.7, Opus 4.6, Sonnet 4.6
unless noted). Every row links to the test or probe script that produced
the measurement.

Anthropic 공식 문서의 모든 contract claim과 본 프로젝트 환경(리전
`ap-northeast-2` 및 엔드포인트 cross-check용 `us-east-1` / `us-west-2`;
별도 명시 없으면 Opus 4.7 / Opus 4.6 / Sonnet 4.6)에서 Bedrock을 실제 호출
했을 때 관측된 동작을 row 단위로 비교한 reference. 각 row는 측정을 생성한
test 또는 probe 스크립트로 링크됩니다.

---

# English

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

### A-2. ❗ Computer use rejected on Bedrock Invoke API for all 3 models

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Tools → Client-side tools table | Computer use listed as `bedrockBeta` for `claudeApiBeta bedrockBeta vertexAiBeta azureAiBeta` (no model qualifier) |
| Our measurement | `tests/unsupported/test_computer_use_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 ALL return 400 rejecting `computer-use-2025-01-24`. The `anthropic-beta: computer-use-2025-01-24` header is not honored on `bedrock-runtime` Invoke API. Verified 2026-05-04. |

The overview's `bedrockBeta` cell led prior matrix passes to mis-categorize
this row as Opus-4.7-specific (see §E). Reality: rejection is universal
across all three measured models on the Invoke API. The "Beta" tag in the
overview applies to the Mantle endpoint, which this suite does not exercise.

### A-3. ❗ Tool search rejected on Bedrock Invoke API for all 3 models

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Tool infrastructure table | Tool search listed as `bedrock` (GA) for `claudeApi bedrock vertexAi azureAiBeta` (no qualifier or beta tag) |
| Our measurement | `tests/unsupported/test_tool_search_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 ALL return 400 rejecting the `tool-search-tool-2025-09-25` tool spec on `bedrock-runtime`. Verified 2026-05-04. |

Same pattern as A-2 (universal rejection on Invoke). Stronger discrepancy
than A-2 because the overview marks this GA, not Beta — a user who reads
only the overview has no signal that the GA path differs from the Invoke
path. Like A-2, this row was previously framed as Opus-4.7-specific in §E.

### A-4. ❗ Compaction beta header rejected on Bedrock Invoke API for all 3 models

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management table | Compaction listed as `bedrockBeta` for all four platforms; note "Supported on Opus 4.7, Opus 4.6, and Sonnet 4.6" |
| Our measurement | `tests/unsupported/test_compaction_header_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 ALL return 400 with "invalid beta flag" for the `anthropic-beta: context-management-2025-06-27` header on `bedrock-runtime` Invoke API. Verified 2026-05-04. |

Important nuance: the related `context_editing` feature (different beta
header — `tests/messages/test_context_editing_works.py`) IS 🟢 across all 3
models. So Bedrock supports SOME context-management features but
specifically rejects the compaction beta header. The overview's single
"Compaction = bedrockBeta" cell hides this distinction.

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
- `CLAUDE_CODE_USE_MANTLE=1` — **explicit opt-in**; mutually exclusive
  with `CLAUDE_CODE_USE_BEDROCK=1` (Invoke API). Without this env var,
  Claude Code on Bedrock always goes through the Invoke API path — which
  is what the matrix in this suite measures. Mantle is **never** a
  default; users land there only by deliberate configuration.
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
| ~~Computer use~~ rejected — **NOT Opus-4.7-specific**: rejection applies to all 3 models on Invoke. Moved framing to §A-2 | Docs `bedrockBeta` cell is Mantle-only | `tests/unsupported/test_computer_use_rejected.py` |
| ~~Tool search~~ rejected — **NOT Opus-4.7-specific**: rejection applies to all 3 models on Invoke. Moved framing to §A-3 | Docs `bedrock` (GA) cell is Mantle-only | `tests/unsupported/test_tool_search_rejected.py` |

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
- 2026-05-04 — re-verified against `results/matrix-2026-05-04.{json,md}`.
  Added §A-2 (Computer use), §A-3 (Tool search), §A-4 (Compaction beta
  header) after a fresh comparison against the
  `build-with-claude/overview` page on platform.claude.com showed all three
  features are listed for `bedrock` / `bedrockBeta` without endpoint
  qualifier but reject on Invoke API for all 3 models. §E rows for
  Computer use / Tool search updated with cross-references to A-2 / A-3
  (rejection is universal, not Opus-4.7-specific).
- All inline numbers above were re-verified against `results/matrix.json`
  on the date stamped at the top of `results/latest.md`.

---

# 한국어

## 측정 범위

본 문서의 모든 "측정" row는 기존 `bedrock-runtime` 엔드포인트의 InvokeModel
API (`/model/{id}/invoke` 또는 `.../invoke-with-response-stream`)를 Anthropic
Python SDK로 호출한 결과를 가리킵니다. `bedrock-mantle` 엔드포인트는 의도적으로
본 suite 범위 밖입니다 (§"설정 정보 (Mantle은 본 suite 범위 밖)" 참조). 본
문서에서 "Bedrock이 X를 거부함" 또는 "Bedrock이 X를 지원함"으로 적힌 모든
표현은, 명시적으로 다른 대안을 언급하지 않는 한 "`ap-northeast-2`에서
Bedrock-runtime InvokeModel이 X를 거부/지원함"으로 읽으시면 됩니다.

## 표기 규약

- 🟢 **일치 (지원)** — docs는 지원이라 명시, 실측이 확인.
- ⛔ **일치 (거부)** — docs는 미지원이라 명시, 실측이 거부 확인.
- 🟡 **docs nuance** — docs가 틀린 건 아니나 해석이 필요; 실제로 기능을 받는
  layer/endpoint/model이 단순 표 cell이 시사하는 범위보다 좁음.
- ❗ **불일치** — docs와 실측이 진짜로 다름.

---

## A. 진짜 불일치 (docs ≠ 실측)

### A-1. ❗ Bedrock의 1시간 prompt cache TTL

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management 표 | `Prompt caching (1hr)`이 `claudeApi`, `vertexAi`, `azureAiBeta`에 대해 표기됨. **`bedrock` token 누락.** |
| `code.claude.com/docs/en/amazon-bedrock` "Pin model versions" | `ENABLE_PROMPT_CACHING_1H=1` env var가 Claude Code on Bedrock 용으로 문서화됨. |
| 실측 | `tests/caching/test_ttl_1h.py` + `results/variability_probe.json`: `ap-northeast-2`의 Opus 4.7에서 5/5 cold-start 시도가 `usage.cache_creation.ephemeral_1h_input_tokens`를 채움. Opus 4.6과 Sonnet 4.6도 동일하게 통과. 5m+1h 혼합 요청은 두 버킷을 독립 추적 (`tests/caching/test_ttl_mixed.py`). |

두 docs 페이지가 1h caching이 Bedrock에서 가능한지에 대해 서로 모순됩니다.
Bedrock 전용 Claude Code docs는 opt-in env var를 문서화하는 반면, platform
전체 overview 표는 Bedrock을 1h row에서 누락합니다. 실측은 env-var 문서와
일치하며, overview 표와는 불일치합니다.

이는 overview 표가 Bedrock 지원을 *과소* 표기함을 의미합니다. overview만 읽은
사용자는 Bedrock = 5m only로 결론짓겠지만, 실제는 5m이 default이고 1h는
opt-in으로 작동합니다.

### A-2. ❗ Computer use는 Bedrock Invoke API에서 3개 모델 모두 거부됨

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Tools → Client-side tools 표 | Computer use가 `claudeApiBeta bedrockBeta vertexAiBeta azureAiBeta`에 대해 `bedrockBeta`로 표기 (모델 qualifier 없음) |
| 실측 | `tests/unsupported/test_computer_use_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 모두 400으로 `computer-use-2025-01-24`을 거부. `anthropic-beta: computer-use-2025-01-24` header는 `bedrock-runtime` Invoke API에서 honor되지 않음. 2026-05-04 검증. |

overview의 `bedrockBeta` cell 때문에 이전 매트릭스 pass에서 본 row를
Opus-4.7-specific으로 잘못 분류했습니다 (§E 참조). 실제: 거부는 측정한 3개
모델 모두에 보편적으로 적용되며 Invoke API 한정. overview의 "Beta" tag는 본
suite가 측정하지 않는 Mantle 엔드포인트에 적용되는 것입니다.

### A-3. ❗ Tool search는 Bedrock Invoke API에서 3개 모델 모두 거부됨

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Tool infrastructure 표 | Tool search가 `claudeApi bedrock vertexAi azureAiBeta`에 대해 `bedrock` (GA, qualifier/beta tag 없음)로 표기 |
| 실측 | `tests/unsupported/test_tool_search_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 모두 400으로 `tool-search-tool-2025-09-25` tool spec을 `bedrock-runtime`에서 거부. 2026-05-04 검증. |

A-2와 동일한 패턴 (Invoke 한정 보편 거부). overview가 GA로 표기 (Beta 아님)
하기 때문에 A-2보다 더 강한 discrepancy입니다 — overview만 읽은 사용자는 GA
path와 Invoke path가 다르다는 신호를 전혀 받지 못합니다. A-2와 마찬가지로
§E에서 Opus-4.7-specific으로 잘못 분류되어 있던 row.

### A-4. ❗ Compaction beta header는 Bedrock Invoke API에서 3개 모델 모두 거부됨

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management 표 | Compaction이 4개 platform 모두에 대해 `bedrockBeta`로 표기. note: "Supported on Opus 4.7, Opus 4.6, and Sonnet 4.6" |
| 실측 | `tests/unsupported/test_compaction_header_rejected.py` — Opus 4.7 / Opus 4.6 / Sonnet 4.6 모두 400과 함께 `bedrock-runtime` Invoke API에서 `anthropic-beta: context-management-2025-06-27` header를 "invalid beta flag"로 거부. 2026-05-04 검증. |

중요한 nuance: 관련 `context_editing` 기능 (다른 beta header —
`tests/messages/test_context_editing_works.py`)은 3개 모델 모두 🟢 입니다.
즉 Bedrock은 일부 context-management 기능은 지원하면서 compaction 전용 beta
header만 specific하게 거부합니다. overview의 단일 "Compaction = bedrockBeta"
cell이 이 구분을 가립니다.

---

## B. 문서 nuance (잘못은 아니나 해석 필요)

### B-1. 🟡 Opus 4.7의 Structured outputs (Bedrock Invoke API)

| Source | Claim |
| --- | --- |
| `build-with-claude/structured-outputs` | "Amazon Bedrock: Generally available for Opus 4.6, Sonnet 4.6, Sonnet 4.5, Opus 4.5, Haiku 4.5. **Opus 4.7 ... available through Claude in Amazon Bedrock (the Messages-API Bedrock endpoint)**" — 즉 Mantle 경유. |
| 실측 (Invoke API) | `tests/messages/test_structured_outputs.py` — Opus 4.6 / Sonnet 4.6은 `output_config.format`을 수용하고 schema 준수 JSON을 반환. Opus 4.7은 `output_config.format: Extra inputs are not permitted`을 반환. |

docs는 표준 Bedrock Invoke API path 기준 기술적으로 정확합니다: 기능은 Opus
4.6 / Sonnet 4.6에서 GA이며 Opus 4.7은 Invoke API에 노출되지 않습니다. Opus
4.7의 경우 docs가 Mantle 엔드포인트로 안내하지만 — **comparison doc상 Mantle은
`ap-northeast-2`에 배포되어 있지 않으므로**, 본 리전 사용자는 globally "GA"
임에도 불구하고 Opus 4.7 + structured outputs에 대한 working path가 없는
상태입니다. Mantle 13개 리전 중 어느 한 곳 (예: `us-east-1`, `ap-northeast-1`
Tokyo)에서는 docs path가 동작해야 하지만, 본 suite는 그것을 측정하지 않습니다.
[설정 정보](#설정-정보-mantle은-본-suite-범위-밖) 참조.

### B-2. 🟡 Strict tool use (`tools[].strict=True`)

Invoke API상에서 B-1과 같은 모델별 패턴. `tests/tools/test_strict_tool_use.py`:

- 🟢 Opus 4.6 / Sonnet 4.6 on Invoke API — 수용, schema 준수 tool input 생성.
- ⛔ Opus 4.7 on Invoke API — `tools.0.custom.strict: Extra inputs are not permitted`로 거부.

### B-3. 🟡 Bedrock의 Token counting — 두 API가 같은 이름 공유

| Source | Claim |
| --- | --- |
| `build-with-claude/overview` Context management 표 | `Token counting`이 `claudeApi bedrock vertexAi azureAiBeta`에 대해 표기. |
| Anthropic SDK (`messages.count_tokens`) | 모든 Bedrock 모델에서 `"Token counting is not supported in Bedrock yet"` 반환. (`tests/token_counting/test_count_tokens.py`) |
| AWS Bedrock-native `CountTokens` API | `/model/{id}/count-tokens`에서 도달 가능. Probe (`scripts/probe_token_counting.py`)는 `User ... is not authorized to perform: bedrock:CountTokens`와 함께 403 반환 — IAM 권한이 게이팅하는 것이지 기능 부재가 아님을 입증. |

docs row "Bedrock 지원"은 Anthropic SDK의 `count_tokens()` 메서드와는 독립적인
AWS-native `CountTokens` API를 가리킵니다. 두 다른 API가 같은 이름을 공유합니다.
SDK-layer 거부는 docs 오류가 아니라 layer-level gap이며, 곧 close될 예정입니다
(SDK 메시지가 literally "yet"이라 적혀 있음).

### 설정 정보 (Mantle은 본 suite 범위 밖)

본 verification suite는 Mantle 엔드포인트 contract를 명시적으로 측정하지
**않습니다**. 그러나 Mantle을 *사용하고자* 하는 reader가 올바른 hostname,
regional availability, 접근 prerequisite을 알 수 있도록 충분한 설정 정보를
이 절에 노출합니다.

Bedrock 엔드포인트 shape에 관한 internal authoritative reference는
[`docs/bedrock-api-endpoints-comparison.md`](../docs/bedrock-api-endpoints-comparison.md)
이며, 3개 엔드포인트 (`bedrock` control plane, `bedrock-runtime` inference,
`bedrock-mantle` inference)와 Bedrock이 노출하는 5가지 API 패턴 (Responses,
Chat Completions, Messages, Converse, InvokeModel)을 catalog합니다. 아래 요약은
본 suite가 왜 Mantle을 skip하는지 이해하기에 충분하며, 전체 coverage는 그
doc을 참조하세요.

**Hostname 차이** (다른 도메인 suffix AND subdomain):

```
Invoke API: bedrock-runtime.{region}.amazonaws.com
Mantle:     bedrock-mantle.{region}.api.aws
```

이 프로젝트의 이전 pass에서 `bedrock-runtime.../v1/messages`를 hit해서
`UnknownOperationException`을 받은 적이 있습니다. 그건 *wrong-host*
artifact였습니다 — `/v1/messages` path는 Invoke host가 아니라 Mantle host에
존재합니다. 올바른 Mantle host를 쓰면 이전에 관측된
`UnknownOperationException`은 다음 중 하나로 resolve됩니다: 진짜 응답, IAM
auth 실패, allowlist 거부, 또는 region-not-deployed 오류 — 환경에 따라 다름.

**Mantle 리전 가용성** (internal comparison doc 기준, 2026-05-03 시점 13 리전):

```
us-east-1, us-east-2, us-west-2,
ap-northeast-1 (Tokyo), ap-south-1 (Mumbai),
ap-southeast-2 (Sydney), ap-southeast-3 (Jakarta),
eu-central-1 (Frankfurt), eu-west-1, eu-west-2,
eu-south-1, eu-north-1,
sa-east-1
```

**`ap-northeast-2` (Seoul)는 이 list에 없습니다.** 본 프로젝트는 Seoul에서
동작하므로, Mantle은 아예 도달 불가능 — allowlist 문제가 아니라 단순 regional
non-deployment입니다. Opus 4.7 + structured outputs는 Mantle이 Seoul에 ship될
때까지 *이 region에서* 작동하는 Bedrock path가 없습니다.

**Mantle의 모델 게이팅** (비대칭):
- 양쪽 엔드포인트: Claude Haiku 4.5, Claude Opus 4.7, Mythos Preview
  (Mythos는 Mantle-only), 다수의 third-party 모델 (DeepSeek, Gemma, Mistral,
  Qwen 등).
- `bedrock-runtime` 한정: Claude Opus 4.1 / 4.5 / 4.6, Claude Sonnet 4 / 4.5
  / 4.6, 모든 Amazon Nova/Titan, Cohere, Llama, embedding 모델, 이미지 생성
  모델. 이들은 Mantle이 배포된 리전에서도 Mantle에서 실행 불가.

이것이 우리 테스트 결과가 일관되었던 이유입니다: Opus 4.6 / Sonnet 4.6은 (가용
엔드포인트가 `bedrock-runtime`뿐이므로) 거기서 structured outputs가 동작하고,
Opus 4.7은 `bedrock-runtime`에서 거부합니다 (해당 기능에 대해 Mantle을
expect함).

**Mantle용 인증**: Bedrock API Key (Bearer) *또는* AWS credentials with SigV4.
`bedrock-runtime`은 AWS credentials만 수용; Bedrock API Key는 Mantle에서
작동하지만 Invoke API의 streaming `/model/{id}/invoke-with-response-stream`
path에서는 일부 환경에서 작동하지 않음 — 환경별 검증 필요.

**Mantle 사용을 위한 Claude Code env vars**:
- `CLAUDE_CODE_USE_MANTLE=1` — **명시적 opt-in**; `CLAUDE_CODE_USE_BEDROCK=1`
  (Invoke API)과 상호배타. 이 env var 없이 Claude Code on Bedrock은 항상
  Invoke API path를 통과 — 이것이 본 suite의 매트릭스가 측정하는 surface
  입니다. Mantle은 **결코** default가 아니며, 사용자는 의도적 설정을 통해서만
  Mantle에 land합니다.
- `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` — host override (gateway가 Mantle 앞에
  있을 때, 또는 Mantle 엔드포인트가 `AWS_REGION`과 다른 리전을 강제할 때 유용).

본 verification suite에 Mantle을 추가하는 것은 현 pass의 범위 밖입니다. 향후
pass에서 다룬다면 위 13 리전 중 하나의 `bedrock-mantle.{region}.api.aws`에서
시작하세요 — `bedrock-runtime`이나 `ap-northeast-2`에서가 아니라.

---

## C. 가짜 불일치 (자체 테스트 버그 — 수정됨)

이전 pass에서 docs vs reality 충돌로 분류되었으나, 조사 결과 자체 테스트 코드가
잘못된 shape을 보내고 있었음. 테스트 수정 후에는 docs와 reality가 일치합니다.

### C-1. ✅ Structured outputs "Bedrock에서 거부됨"

- 옛 테스트 (`tests/unsupported/test_structured_outputs_response_format_rejected.py`,
  제거됨)는 `response_format` (OpenAI 스타일 필드명)을 보냈습니다. Anthropic
  API에는 그 필드가 없으므로, 거부 `"response_format: Extra inputs are not
  permitted"`은 unknown-field error였지 feature-rejection이 아니었습니다.
- 새 테스트 (`tests/messages/test_structured_outputs.py`)는 `output_config.format`
  (현재 Anthropic GA 파라미터)을 사용. 진짜 모델별 contract를 확인합니다 —
  B-1 참조.

### C-2. ✅ Strict tool use "Bedrock에서 거부됨"

- 옛 테스트는 Bedrock에서의 일괄 거부를 단언했으나, 실제 API는 Opus 4.6과
  Sonnet 4.6에서 `strict=True`를 수용했습니다. 결과: 옛 매트릭스 run에서 두
  모델은 ❌. 테스트가 잘못된 contract를 단언하고 있었던 것. Opus 4.7의 거부는
  진짜였지만 테스트가 잘못 일반화한 것이었습니다.
- 새 테스트 (`tests/tools/test_strict_tool_use.py`)는 모델별 적응형. B-2 참조.

---

## D. 일치 (불일치 없음)

완전성을 위해, 본 프로젝트가 측정한 나머지 surface에 대해서는 docs feature
표가 정확하게 동작을 예측합니다:

- **Prompt caching (5m)** — docs와 `tests/caching/test_on_messages.py` 등에
  따라 Bedrock에서 지원.
- **Multi-breakpoint cache** — `tests/caching/test_multi_breakpoint.py` 기준
  지원.
- **`extended-cache-ttl-2025-04-11` beta header** — 통상적 read 기준
  Anthropic-only; Bedrock은 "invalid beta flag" 반환
  (`tests/caching/test_extended_ttl_header_rejected.py`).
- **Server-side tools** (web search / code execution / web fetch / memory
  server tool / MCP connector / Files API / Batches / Computer use) — docs는
  이들을 Anthropic-API-direct 또는 claudeApiBeta로 표기, 우리
  `tests/unsupported/` 디렉토리가 Bedrock에서의 거부를 확인.
- **Streaming**, **PDF**, **citations**, **vision**, **multi-turn**,
  **1M context**, **adaptive thinking**, **interleaved thinking** — 모두
  docs와 일치.
- **Bash / memory / text editor client-side tools** — docs와 일치.

---

## E. Opus 4.7 specific contract changes (docs는 언급하지만 "feature available" 표가 오해 유발)

일반 feature 표는 row를 모델별로 split하지 않습니다. 다음 contract 변경은
Opus 4.7에 specific하게 적용되며, "Bedrock-listed feature는 그냥 다 동작한다"
고 가정한 reader를 surprise하게 만들 것입니다:

| Surface | Docs note 존재? | 우리 테스트 |
| --- | --- | --- |
| Sampling 파라미터 (`temperature` / `top_p` / `top_k`) deprecated → 400 | Implicit (release notes) | `tests/messages/test_sampling_deprecated.py` |
| `thinking.type=enabled` 거부; `adaptive` + `output_config.effort` 사용 | Docs는 adaptive를 "Opus 4.7 권장 thinking mode"로 flag | `tests/thinking/test_enabled_with_effort.py` |
| Assistant prefill (trailing assistant message) 거부 — "must end with a user message" | Prominently flag되지 않음 | `tests/messages/test_assistant_prefill.py` |
| `output_config.format` Invoke API에서 거부 | Implicit (structured-outputs 페이지의 Mantle requirement note) | `tests/messages/test_structured_outputs.py` |
| `tools[].strict=true` Invoke API에서 거부 | 동일 | `tests/tools/test_strict_tool_use.py` |
| ~~Computer use~~ 거부 — **Opus-4.7-specific 아님**: 거부는 3개 모델 모두 Invoke에 적용. Framing은 §A-2로 이동 | Docs `bedrockBeta` cell은 Mantle-only | `tests/unsupported/test_computer_use_rejected.py` |
| ~~Tool search~~ 거부 — **Opus-4.7-specific 아님**: 거부는 3개 모델 모두 Invoke에 적용. Framing은 §A-3로 이동 | Docs `bedrock` (GA) cell은 Mantle-only | `tests/unsupported/test_tool_search_rejected.py` |

이 모두는 더 큰 theme을 따릅니다: Opus 4.7은 docs 표의 같은 Bedrock cell 내에서
더 구버전 Bedrock 모델보다 narrower한 contract surface를 갖습니다.

---

## F. 각 row 재현 명령

```bash
# Caching contract (1h finding A-1 포함)
python run_all.py --all-models --only caching

# Structured outputs (B-1, C-1)
python run_all.py --all-models --only-tests structured_outputs
python scripts/probe_structured_outputs.py

# Strict tool use (B-2, C-2)
python run_all.py --all-models --only-tests strict_tool_use

# Token counting (B-3)
python run_all.py --only-tests count_tokens
python scripts/probe_token_counting.py

# Mantle 엔드포인트 — 본 suite 범위 밖. 위 "설정 정보 (Mantle은 본 suite 범위 밖)"
# 에서 올바른 host (bedrock-mantle.{region}.api.aws)와 접근 prerequisite 참조.

# Claude Code wire-level 캡처 (이 매트릭스와 cross-reference)
python scripts/intercept_proxy.py &
ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001 \
  CLAUDE_CODE_USE_BEDROCK=1 claude -p "..."
```

모든 측정은 `AWS_BEARER_TOKEN_BEDROCK`이 set된 상태에서 재현 가능.

---

## G. Last reviewed

- 2026-05-03 — docs와 매트릭스 사이의 초기 cross-walk.
- 2026-05-04 — `results/matrix-2026-05-04.{json,md}` 기준 재검증.
  platform.claude.com의 `build-with-claude/overview` 페이지에 대한 fresh 비교
  결과, 3개 기능이 endpoint qualifier 없이 `bedrock` / `bedrockBeta`로 표기되어
  있으나 Invoke API에서 3개 모델 모두 거부됨이 드러나 §A-2 (Computer use),
  §A-3 (Tool search), §A-4 (Compaction beta header)을 추가. §E의 Computer
  use / Tool search row는 거부가 보편적 (Opus-4.7-specific 아님)이므로 §A-2
  / §A-3로 cross-reference 갱신.
- 위 모든 inline number는 `results/matrix.json`의 `results/latest.md` 상단에
  stamp된 날짜 기준 재검증됨.
