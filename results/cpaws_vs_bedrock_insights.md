# CPaws vs Bedrock — Detailed Cross-Provider Insights

> Empirical analysis of the 2026-05-20 cross-provider matrix run
> (`results/runs/2026-05-20/`). Bilingual — English first, 한국어 below.
> Companion to `results/cpaws_findings.md` which carries the §A/B/C/D/E
> structured findings; this document layers strategic interpretation on
> top of those raw findings.

## 0. Table of contents

1. [Executive summary](#1-executive-summary)
2. [Quantitative overview](#2-quantitative-overview)
3. [CPaws unique value — 6 surfaces only on CPaws](#3-cpaws-unique-value)
4. [Anthropic-level gates — 6 surfaces both providers reject](#4-anthropic-level-gates)
5. [Behavioral divergences — same surface, different runtime](#5-behavioral-divergences)
6. [Category-level disagreement concentration](#6-category-level-disagreement)
7. [Operational dimensions — auth, tier, SDK](#7-operational-dimensions)
8. [Token economics and cost implications](#8-token-economics)
9. [Provider selection framework](#9-provider-selection-framework)
10. [What this matrix does NOT measure](#10-what-this-matrix-does-not-measure)
11. [Strategic implications](#11-strategic-implications)
12. [Recommendations by workload type](#12-recommendations-by-workload-type)

---

## 1. Executive summary

The 2026-05-20 matrix tested 57 contract probes across 4 cells
(2 providers × 2 models). Headline:

- **Both providers agree on the core Messages API surface (~75% of
  probes)** — basic generation, streaming, tools, citations, documents,
  vision, multilingual all behave identically on Bedrock and CPaws.
- **CPaws unlocks 6 surfaces that Bedrock rejects** — count_tokens,
  server tools (web_search/web_fetch/code_execution), strict tool use
  on Opus 4.7, structured outputs on Opus 4.7, Anthropic-direct
  endpoints (`messages.batches`, `models.list`), and the extended cache
  TTL beta header.
- **6 surfaces are gated by Anthropic itself** and remain ⛔ on both
  providers — switching providers does not unlock them (computer_use,
  tool_search, compaction beta, assistant_prefill on Opus 4.7, sampling
  param deprecation, `thinking.enabled_with_effort` on Opus 4.7).
- **2 subtle behavioral divergences exist on shared surfaces** —
  `cache_ttl_1h` second-call cache bucket allocation differs, and
  short-response streaming chunking granularity differs.
- **CPaws Tier 1 imposes a hard 30k input TPM ceiling per workspace**
  that single large requests can exceed, producing 429 RateLimitError
  that no retry escape — pdf and 1M-context probes failed on
  `cpaws/sonnet-4-6` for this reason, NOT contract issues.

**TL;DR**: CPaws is a *superset* of Bedrock for the Messages API
surface (6 additional features) with *near-identical* runtime behavior
on shared surfaces (2 measurable but minor differences). The decision
between them rests on operational factors (auth, billing, tier),
not on capability per se.

---

## 2. Quantitative overview

### 2.1 Per-cell totals

| Cell | 🟢 Supported | ⛔ Rejected (contract) | ❌ Fail | Total |
|---|---:|---:|---:|---:|
| `bedrock/opus-4-7` | 45 | 12 | 0 | 57 |
| `bedrock/sonnet-4-6` | 48 | 9 | 0 | 57 |
| `cpaws/opus-4-7` | 47 | 6 | 4 | 57 |
| `cpaws/sonnet-4-6` | 44 | 5 | 8 | 57 |

### 2.2 Effective coverage (after ❌ classification)

The raw matrix understates CPaws coverage because the project's probe
assertions are largely shaped around Bedrock contracts. The MANIFEST.md
companion to each matrix re-classifies ❌ into three buckets:

| Cell | Raw 🟢 | + ❌-as-🟢 (contract divergence captured) | − Tier 1 RL ❌ | Effective coverage |
|---|---:|---:|---:|---:|
| `bedrock/opus-4-7` | 45 | 0 | 0 | 45/57 = 79% |
| `bedrock/sonnet-4-6` | 48 | 0 | 0 | 48/57 = 84% |
| `cpaws/opus-4-7` | 47 | +3 | 0 | **50/57 = 88%** |
| `cpaws/sonnet-4-6` | 44 | +3 | 3 are RL, not contract | **47/57 = 82%** (or 47/54 = 87% excluding RL) |

**Reading**: CPaws supports MORE of the tested surfaces than Bedrock —
the optical impression of "more ❌ means worse" is wrong. The probes
that ❌ on CPaws are mostly *signals that CPaws supports something
Bedrock does not* — the probe's pass-condition assumed Bedrock
rejection.

### 2.3 Cross-provider divergence count

16 (test, model) pairs diverge between providers across 11 unique tests:

```
unsupported       6 divergent pairs / 5 probes in category
caching           2 divergent pairs / 8 probes
token_counting    2 divergent pairs / 1 probe  (both models)
documents         2 divergent pairs / 2 probes (Tier 1 RL on sonnet)
messages          1 divergent pair  / 11 probes
tools             1 divergent pair  / 11 probes
context           1 divergent pair  / 2 probes
streaming         1 divergent pair  / 5 probes
```

**Observation**: divergence concentrates in `unsupported/`, `caching/`,
`token_counting/`, `documents/`. The 4 categories representing
"boundary surfaces" (admin-shaped features, cache mechanics, token
introspection, document handling) drive almost all cross-provider
decisions. The 5 categories `messages`, `tools`, `multilingual`,
`vision`, `citations` — the "everyday API" — converge.

---

## 3. CPaws unique value

The 6 surfaces below FAIL on Bedrock and WORK on CPaws. They are the
*concrete answer* to "why add CPaws as a delivery channel?".

### 3.1 `messages.count_tokens`

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/token_counting/count_tokens.py` | ⛔ rejected (`InternalServerException` or absent) | 🟢 returns input_tokens count |

**Why it matters**: Without `count_tokens`, you cannot estimate prompt
token usage before submitting a request. This forces approximations
(tiktoken or similar) that don't match Anthropic's actual tokenizer.
CPaws gives the canonical answer, useful for:
- Cost estimation before submission
- Sliding-window prompt construction
- Cache-key engineering (knowing exact token boundary)

### 3.2 Server tools — web_search / web_fetch / code_execution

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/unsupported/server_tools.py` | ⛔ all 3 tool types rejected | 🟢 all 3 accepted *and execute* |

**Functional verification (from `cpaws_findings.md §A.6`, 2026-05-12)**:
- `web_search` query "Who won the 2025 Nobel Prize in Physics?" →
  returned real laureates (John Clarke, Michel H. Devoret,
  John M. Martinis). Token usage: 20,394 input + 880 output.
- `web_fetch` URL `https://www.anthropic.com` → returned real page
  with canonical URL and meta-description. Token usage:
  8,439 input + 108 output.
- Results delivered as `encrypted_content` blocks (model-only
  decryption).

**Why it matters**: These tools let the model perform actions in the
model's own turn — no external orchestration needed. The Bedrock
alternative is to implement client-side tools and route results back
via tool_use_id, which doubles the round-trip count and exposes
unencrypted content.

### 3.3 Strict tool use (`strict_tool_use=True`) on Opus 4.7

| Probe | Bedrock opus-4-7 | CPaws opus-4-7 |
|---|---|---|
| `probes/tools/strict_tool_use.py` | ⛔ rejected (`output_config.format: Extra inputs are not permitted` shape) | 🟢 supported |

**Note**: Sonnet 4.6 supports this on BOTH providers — divergence is
Opus 4.7-specific. The recommended path for Opus 4.7 strict tool use on
Bedrock is via the Mantle endpoint, which is out of scope for this
suite (see `results/docs_vs_reality.md`).

**Why it matters**: Strict tool use guarantees the JSON arguments to a
tool call conform exactly to the declared schema, eliminating the
"function called with malformed args" failure mode that requires
client-side parsing-and-retry.

### 3.4 Structured outputs (`output_config.format`) on Opus 4.7

| Probe | Bedrock opus-4-7 | CPaws opus-4-7 |
|---|---|---|
| `probes/messages/structured_outputs.py` | ⛔ rejected | 🟢 returns schema-conformant JSON |

Same pattern as 3.3 — sonnet works on both, opus-4-7 diverges. The
runtime contract is "response strictly conforms to declared JSON
schema". Without this, you need `try/except json.JSONDecodeError` +
re-prompting cycles.

### 3.5 Anthropic-direct endpoints

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/unsupported/endpoints_absent.py` for `messages.batches` | ⛔ attribute absent | 🟢 callable |
| `probes/unsupported/endpoints_absent.py` for `models.list()` | ⛔ attribute absent | 🟢 returns 6 models (verified 2026-05-20) |

**`models.list()` output on CPaws** (2026-05-20):
```
claude-opus-4-7
claude-sonnet-4-6
claude-opus-4-6
claude-opus-4-5-20251101
claude-haiku-4-5-20251001
claude-sonnet-4-5-20250929
```

**Why it matters**: Dynamic model discovery (don't hardcode model IDs),
batch submission for high-throughput offline processing, and admin-
shaped flows are available on CPaws. Bedrock equivalents exist via
`boto3 bedrock` (separate API), not via the `anthropic` SDK.

### 3.6 `extended-cache-ttl-2025-04-11` beta header

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/caching/extended_ttl_header_rejected.py` | ⛔ "invalid beta flag" | 🟢 header accepted |

**Note**: The 2026-05-20 matrix shows this aligned (both ⛔ via the
test's contract-divergent encoding). Underlying behavior unchanged
since 2026-05-12.

### 3.7 The model-tier convergence pattern

In §3.3 and §3.4, sonnet-4-6 has aligned with CPaws semantics on
Bedrock too. Three hypotheses:

1. **Differential rollout**: Anthropic ships features to sonnet first,
   opus follows on a different cadence
2. **Opus 4.7 special policy**: Opus 4.7 routes through a different
   endpoint group (Mantle) on Bedrock
3. **Beta feature graduation**: Features that were CPaws-only graduate
   to all providers as they mature

This implies: **switching from opus-4-7 to sonnet-4-6 on Bedrock
unlocks 2 of the 6 §A surfaces** without changing provider.

---

## 4. Anthropic-level gates

The 11 (test, model) pairs where BOTH providers reject. Map to 5
unique surfaces. Moving from Bedrock to CPaws does NOT unlock these.

| Surface | Models | Reason | Unblockable? |
|---|---|---|---|
| `computer_use_20250124` | both | Anthropic gates desktop automation | No |
| `tool_search_*` | both | Separate product channel; not generally available | No |
| `assistant_prefill` (response prefix) on Opus 4.7 | opus-4-7 | Deprecated globally on Opus 4.7 family | No |
| Sampling params (`temperature`/`top_p`/`top_k`) deprecation | both models for Opus 4.7 | Global deprecation | No |
| `thinking.enabled_with_effort` | Opus 4.7 only | Migrated to `adaptive` globally | No |

### 4.1 Cost of NOT knowing about §B

A team contemplating "move from Bedrock to CPaws to gain X" must check
X against §B first. The matrix surfaces this cleanly — but it requires
running the suite on BOTH providers to detect. A single-provider matrix
would incorrectly attribute these rejections to Bedrock-specifically.

### 4.2 The Opus 4.7 sampling deprecation is worth highlighting

Three surfaces ⛔ on Opus 4.7 across BOTH providers:
- `assistant_prefill`
- `sampling_params_deprecated`
- `thinking.enabled_with_effort`

This points to **Opus 4.7 having a tighter contract surface than Opus
4.6/Sonnet 4.6**. If your codebase relies on these knobs, **stay on
Opus 4.6 or migrate to Sonnet 4.6**, regardless of provider.

---

## 5. Behavioral divergences

Surfaces accepted on BOTH providers but exhibiting **different runtime
behavior**. The most dangerous category — code that ran fine on
Bedrock may produce subtly different observable behavior on CPaws (or
vice versa) without triggering an obvious error.

### 5.1 `cache_ttl_1h` — second-call cache bucket allocation

**Bedrock (both models, ap-northeast-2)**:
```
First call:  cache_creation.ephemeral_1h_input_tokens = 15,025
             cache_read_input_tokens                  = 0
Second call: cache_creation.ephemeral_1h_input_tokens = 0
             cache_read_input_tokens                  = 15,025
             ← Clean: 1h bucket read, no new writes
```

**CPaws (both models, us-east-2)**:
```
First call:  cache_creation.ephemeral_1h_input_tokens = 15,021
             cache_read_input_tokens                  = 0
Second call: cache_creation.ephemeral_5m_input_tokens = 5-8
             cache_read_input_tokens                  = 15,021
             ← 1h read works, but ALSO writes 5-8 new tokens to 5m bucket
```

**Reproducibility**: Confirmed in this 2026-05-20 run on both
`cpaws/opus-4-7` and `cpaws/sonnet-4-6` in us-east-2 — rules out
region or model as sole driver. First documented 2026-05-12 in
ap-northeast-2.

**Cost implications**:
- For one-shot cache reads: negligible (5-8 tokens per second-call).
- For sustained workloads (system-prompt cache reused 1000× per hour):
  5,000-8,000 extra billed tokens per hour, *in addition to* the
  expected cache_read billing.
- Pattern: every "cache hit" on CPaws comes with a tiny mandatory
  write tax.

**Probable cause** (untested hypothesis): CPaws cache layer treats the
non-prefix portion of the second call as a fresh prefix needing its
own cache entry, while Bedrock identifies it as a read-only delta.

**Hypotheses still open** (per `cpaws_findings.md §C.1`):
- Cache propagation delay in CPaws infrastructure
- 1h bucket served from different storage tier than 5m bucket
- Region-specific (initially us-east-2 hypothesis ruled out 2026-05-20)

### 5.2 Streaming chunking granularity for short responses

**Bedrock**: short prompt "reply 1, 2, 3, 4, 5" produces multiple
`RawContentBlockDeltaEvent` events — one per word or per few tokens.

**CPaws**: same prompt produces exactly **one** delta event with the
full text in a single chunk:
```
event_kinds: RawMessageStartEvent, RawContentBlockStartEvent,
             RawContentBlockDeltaEvent (×1), RawMessageDeltaEvent,
             ParsedContentBlockStopEvent, ParsedMessageStopEvent,
             TextEvent
stop_reason: end_turn
preview: "1, 2, 3, 4, 5"
delta_count: 1
```

**UX implications**:
- Final text and `stop_reason` are identical to Bedrock.
- Progressive UI rendering (character-by-character animations,
  word-by-word reveals) will *jump* on CPaws for short responses
  instead of streaming smoothly.
- Long responses likely chunk normally on CPaws (untested — see
  follow-up in `cpaws_findings.md §G`).
- This is *infrastructure-level buffering*, not a model behavior
  difference.

**Detection**: pin `delta_count > N` in stream-aware probes.

---

## 6. Category-level disagreement

The 16 cross-provider (test, model) divergences map to categories
as follows. The shape tells you where provider choice matters most:

```
unsupported     ████████ 6  (probe domain: cross-provider differences)
caching         ██       2  (cache_ttl_1h on both models)
token_counting  ██       2  (count_tokens on both models)
documents       ██       2  (Tier 1 rate limit on sonnet — not contract)
messages        █        1  (structured_outputs on opus-4-7)
tools           █        1  (strict_tool_use on opus-4-7)
context         █        1  (context_1m_beta on sonnet — Tier 1 RL)
streaming       █        1  (delta count on sonnet)
```

**Reading by category**:

| Category | Divergence rate | Interpretation |
|---|---|---|
| `unsupported/` | 6/5 (>100% — multi-model) | This category exists TO encode cross-provider differences. Working as designed. |
| `caching/` | 2/8 = 25% | Provider choice meaningfully affects cache behavior |
| `token_counting/` | 2/1 = 200% (both models) | Single probe, but unique offer of CPaws |
| `documents/` | 2/2 = 100% (sonnet RL) | NOT contract — Tier 1 ceiling on heavy probes |
| `messages/` | 1/11 = 9% | 91% convergent — core API is portable |
| `tools/` | 1/11 = 9% | 91% convergent |
| `multilingual/` | 0/2 = 0% | Identical |
| `vision/` | 0/2 = 0% | Identical |
| `citations/` | 0/2 = 0% | Identical |
| `thinking/` | 0/5 = 0% | Identical |

**Implication**: Code written against the `messages`, `tools`,
`multilingual`, `vision`, `citations`, `thinking`, `client`,
`streaming` categories is **portable between providers with near-zero
adaptation**. Code that hits the `unsupported`, `caching`,
`token_counting`, `documents` boundaries needs provider-aware paths.

---

## 7. Operational dimensions

### 7.1 Authentication

| Dimension | Bedrock | CPaws |
|---|---|---|
| Primary auth | AWS Bearer (`AWS_BEARER_TOKEN_BEDROCK`) | Workspace API key (`x-api-key` + `anthropic-workspace-id` header) |
| Key format | `ABSK` prefix, base64-encoded | `AEAA` prefix, base64-encoded (similar shape) |
| SDK class | `AnthropicBedrock`, `AsyncAnthropicBedrock` | `AnthropicAWS`, `AsyncAnthropicAWS` |
| IAM integration | ✅ Native (Bedrock supports SigV4 + bearer token) | ⚠ SDK supports SigV4 path but workspace key is the documented default |
| Endpoint shape | `bedrock-runtime.<region>.amazonaws.com` | `aws-external-anthropic.<region>.api.aws` |
| Rotation | AWS console, IAM policy | Anthropic console |
| Audit trail | CloudTrail (DataPlane events) | (CPaws-specific — not CloudTrail) |

### 7.2 Rate limit / tier model

| Aspect | Bedrock | CPaws |
|---|---|---|
| Quota mechanism | Per-region AWS service quotas, per model | Anthropic tier system (Tier 1 to 4) per workspace |
| Tier 1 input TPM | (Per AWS service quotas, generally more permissive) | **30,000 input tokens / minute** (measured 2026-05-20) |
| Tier 1 output TPM | (Bedrock model quotas) | Tier-dependent |
| Single-request size ceiling | Bound by model context window, not RL | Single request can exceed minute budget → 429 instantly |
| Burst tolerance | ✅ Region-wide pool | ⚠ Workspace-scoped |
| 529 Overloaded | Rare for general-purpose calls | Observed sustained on Haiku 4.5 during this run |
| Retry behavior | SDK default 2 retries | We bumped to 10 (`providers/cpaws.py`, env `CPAWS_MAX_RETRIES`) |

**Implication of the 30k Tier 1 ceiling**:
- A single PDF probe (~32k input tokens) blocks for the full minute
  budget, returns 429, retries with backoff, may still exceed.
- For workloads with >5k input tokens per call, Tier 1 is insufficient
  for matrix-style serial sweeps.
- Upgrade to Tier 2+ (request via Anthropic console) or split inputs.

### 7.3 SDK / API surface

| Endpoint | Bedrock | CPaws |
|---|---|---|
| `messages.create` | ✅ | ✅ |
| `messages.stream` | ✅ | ✅ (with 5.2 chunking caveat) |
| `messages.count_tokens` | ⛔ | ✅ |
| `messages.batches.*` | ⛔ attribute_absent | ✅ |
| `models.list` | ⛔ attribute_absent | ✅ |
| `files.*` | ⛔ attribute_absent | ⛔ **also absent on CPaws** — SDK version dependency (see §G.5) |
| `admin.*` | (not tested) | (not tested) |
| Async equivalents | `AsyncAnthropicBedrock` | `AsyncAnthropicAWS` |

### 7.4 Billing

| Aspect | Bedrock | CPaws |
|---|---|---|
| Billed through | AWS account (Bedrock service) | AWS Marketplace (Claude on AWS) |
| Token pricing | Bedrock list pricing | Anthropic list pricing × Marketplace markup (verify current) |
| Cache discount | ✅ Documented | ✅ Documented |
| Cross-region cost | Cross-region transfer charges may apply | (Verify per Marketplace contract) |

---

## 8. Token economics

### 8.1 Per-run cost proxy from 2026-05-20

From the per-cell token accumulator output (totals across 57 probes
per cell, NOT directly comparable across cells because failure rate
affects total API calls):

| Cell | Probes that ran | Approximate input billable (k) |
|---|---:|---:|
| `bedrock/opus-4-7` | 57/57 PASS, full token consumption | ~570k (per 2026-05-12 baseline of comparable run) |
| `bedrock/sonnet-4-6` | 57/57 PASS | ~570k |
| `cpaws/opus-4-7` | 57 attempted, 53 settle, 4 ❌ | ~530k |
| `cpaws/sonnet-4-6` | 57 attempted, many retried via 429 | (inflated by SDK retries on rate-limited probes) |

**Caveat**: This matrix is a coverage probe, not a benchmark. Token
costs are dominated by the largest probes (PDF, context_1m), which
makes per-cell totals an *upper bound* indicator only.

### 8.2 Cache cost asymmetry from §5.1

For a hypothetical workload reusing a 15k-token cached prefix
1,000 times per hour:

| Provider | Per-hit billable | 1000 hits / hour billable |
|---|---:|---:|
| Bedrock | ~0 cache_create + 15,025 cache_read | 15,025,000 cache_read tokens |
| CPaws | ~5-8 cache_create (5m bucket) + 15,021 cache_read | 15,021,000 cache_read + 5,000-8,000 cache_create |

**Annualized impact**: ~50-70 million extra cache_create tokens per
year for high-frequency cached-prefix workloads on CPaws. At
$0.30/1M-tok cache_create pricing (representative), that's **~$15-25
extra per year** — small in absolute terms but a systematic tax.

### 8.3 The "free" features have a cost

CPaws's 6 unique surfaces (§3) are not free in API economic terms:
- `count_tokens` calls billed (small)
- Server tools (`web_search` returned 20k input tokens + 880 output;
  per use)
- Batches API has its own billing model (typically discounted, verify)

The point: §3 surfaces unlock *capabilities*, but the rate of using
them affects spend more than the provider switch itself.

---

## 9. Provider selection framework

A decision rubric synthesized from §3–§8:

### 9.1 Choose Bedrock when

- AWS-native integration is load-bearing (VPC endpoints, PrivateLink,
  IAM roles for service-to-service auth)
- Compliance / data residency requires specific AWS regions not yet
  available on CPaws Marketplace
- Existing AWS Cost Explorer / Cost & Usage Report integration
- Single-request payload is large (PDF processing, 1M context probes)
  and Tier 1 ceiling is restrictive
- Want CloudTrail audit trail of API calls
- Need *Mantle endpoint* features (not in this matrix's scope)

### 9.2 Choose CPaws when

- Need `count_tokens` for cost preview / windowing
- Need server tools (`web_search`, `web_fetch`, `code_execution`)
- Need `strict_tool_use` or `structured_outputs` on Opus 4.7
  (and not using Mantle)
- Need batch API for high-throughput offline processing
- Want canonical 1P Anthropic behavior (closest match to direct
  Anthropic API while still on AWS billing)
- Need dynamic model discovery via `models.list()`

### 9.3 Use BOTH when

- Different workloads have different needs (e.g. interactive UI on
  Bedrock, batch enrichment on CPaws)
- Comparing provider behavior is itself the requirement (this matrix)
- Failover or capacity diversification

### 9.4 Neither path unblocks

- `computer_use_20250124` (Anthropic gates)
- `tool_search_*` (separate channel)
- Opus 4.7 `assistant_prefill`, sampling params,
  `thinking.enabled_with_effort` (global deprecation)
- `compaction-2025-09-17` beta (flag not released)

For these, the answer is either "wait" (deprecation reversal unlikely)
or "use a different model family" (Sonnet 4.6 retains some of these).

---

## 10. What this matrix does NOT measure

Honest analysis demands explicit limits. The 2026-05-20 matrix
**does not** measure:

1. **Batches workflow** — `client.messages.batches.*` attribute
   *existence* was tested; batch submit → execute → retrieve flow was
   not exercised. CPaws may behave differently mid-flow.
2. **Files API** — both providers showed `attribute_absent` for
   `client.files.*`. This is likely **SDK version dependency**, not
   server-side absence. Upgrading the `anthropic` package and re-testing
   is `cpaws_findings.md §G.5`.
3. **Admin API** — `client.admin.*` (organization/workspace
   management) not in this suite.
4. **Pricing differential** — no USD-level cost comparison between
   identical token consumption on Bedrock vs CPaws.
5. **Latency** — request-response wall-clock time not benchmarked.
   This matrix's per-probe `elapsed_s` values include retry-after
   sleeps, so they are not clean latency.
6. **Long-term reliability** — single-day snapshot. Anthropic
   capacity events (529 Overloaded) observed on Haiku 4.5 on CPaws
   would need multi-day sampling to characterize.
7. **Cross-region behavior** — CPaws tested on `us-east-2`, Bedrock on
   `ap-northeast-2`. Same region for both not measured this run (it
   was the 2026-05-12 baseline).
8. **High-concurrency workloads** — matrix is serial. Concurrent
   request behavior, especially under Tier 1 limits, may differ.
9. **Streaming behavior on long responses** — §5.2 short-response
   chunking measured; long-response chunking inferred from probe code
   but not specifically compared.
10. **PrivateLink / VPC endpoint paths** — Bedrock supports these;
    CPaws's network path properties not characterized.
11. **Haiku 4.5 baseline on CPaws** — attempted, blocked by sustained
    529. Excluded from `MODEL_ALIASES`. Tier 1 capacity recovery
    required (`cpaws_findings.md §G.6`).
12. **Mantle endpoint** — `bedrock-mantle.<region>.api.aws` is
    explicitly out of scope for this suite (project memory:
    "Mantle is opt-in, not default").

---

## 11. Strategic implications

### 11.1 Two providers are complementary, not competing

The 75% convergence on core Messages API surface means CPaws is NOT
"a different LLM platform" — it is "the same Anthropic models with a
different operational envelope". The competitive frame is wrong; the
*portfolio* frame is right:
- Bedrock: AWS-shaped Anthropic
- CPaws: Anthropic-shaped Anthropic delivered via AWS

Same models, same generation quality, same SLAs (from Anthropic).
Different ergonomics, different feature surface, different auth.

### 11.2 "1P migration" decisioning has a quantified answer now

The pre-matrix question "should we move to 1P (direct Anthropic API)?"
becomes a smaller question on CPaws: "do we need any of the 6 §A
surfaces?". The matrix shows the answer is binary:

- **If yes**: move to CPaws (cheaper than full 1P direct migration —
  same AWS billing, same VPC, same compliance surface).
- **If no**: stay on Bedrock (operational simplicity, broader region
  availability, mature CloudTrail).

The matrix removes the FUD around "are we missing something?".
Answer: 6 specific surfaces, listed by name.

### 11.3 Test suite design as portable insight

The matrix's *meta* value: a portable Python harness that any team can
run against their own workspace credentials to validate the same
findings in their context. Concretely:

- `probes/` is importable as a Python library
- `scripts/rerun_cells.py` regenerates one cell with custom pacing
- `scripts/snapshot_matrix.py` produces dated baselines

Teams can answer "did my workspace's tier limits affect this?",
"does my region show the same behavior?", "did Anthropic change
something this week?" empirically rather than escalating to support.

### 11.4 Probe assertion shape is a leverage point

Recurring lesson from §10 and §6: matrix ❌ counts overstate provider
disagreement because probe assertions encode a single provider's
contract. The MANIFEST `_failure_caveats` classifier is the
*interpretation layer* that converts raw matrix into actual insight.

**Implication**: future probe refactors should encode contracts as
`info.contract = "supported_on_X" / "rejected_on_Y"` (the
`test_sampling_deprecated` pattern), making the runner's classifier
the single source of truth and eliminating the "❌ that's actually 🟢"
discrepancy.

---

## 12. Recommendations by workload type

| Workload | Recommended provider | Reasoning |
|---|---|---|
| Interactive chat UI (real-time SSE rendering, short responses) | **Bedrock** | §5.2 streaming chunking favors Bedrock for progressive UI |
| Batch document processing (PDF, OCR pipelines) | **Bedrock** (single requests) OR **CPaws Tier 2+** (batches API) | Tier 1 ceiling on CPaws blocks single-PDF probes |
| Cost-sensitive prompt engineering (cache + token counting) | **CPaws** | `count_tokens` enables tight budgeting |
| Agentic workflows with web tools | **CPaws** | Server tools (`web_search`, `web_fetch`, `code_execution`) executed natively |
| Structured data extraction (JSON schema) | **CPaws** for Opus 4.7; either for Sonnet 4.6 | `output_config.format` only on CPaws for opus-4-7 |
| High-throughput async / offline | **CPaws** (`messages.batches.*`) | Available via SDK on CPaws only |
| Compliance-heavy (CloudTrail, IAM policies, PrivateLink) | **Bedrock** | Native AWS integration |
| Multi-region active-active failover | **Both** (each provider as backup for the other) | Diversification |
| Strict tool calling on Opus 4.7 | **CPaws** | Bedrock requires Mantle (out of scope here) |
| Long-context (>200k input tokens) on Tier 1 workspace | **Bedrock** | Single-call payload exceeds CPaws Tier 1 minute budget |
| Cache-heavy with 1h TTL prefix reuse | **Bedrock** | §5.1 — no 5m bucket tax on second-call reads |

---

## 13. References

- `results/runs/2026-05-20/matrix.{json,md}` — raw matrix data
- `results/runs/2026-05-20/MANIFEST.md` — failure classification
- `results/runs/2026-05-20/bedrock.md` / `cpaws.md` — per-provider views
- `results/cpaws_findings.md` — §A/B/C/D/E structured findings (baseline 2026-05-12, refreshed 2026-05-20)
- `results/docs_vs_reality.md` — Anthropic public docs vs measured contract
- `results/prompt_caching_verified.md` — cache contract reference with §P-1 cold-start salt evidence
- `probes/` — importable contract probe library
- `config.py` — `MODEL_ALIASES`, `BEDROCK_UNSUPPORTED`
- `providers/cpaws.py` — `max_retries=10` Tier 1 hardening

**Snapshot identity** for this analysis: `git 0c98a88` on `main`,
2026-05-20 UTC.

---

# CPaws vs Bedrock — 상세 cross-provider 인사이트 (한국어)

> 2026-05-20 cross-provider 매트릭스 (`results/runs/2026-05-20/`)
> 기반 분석. `results/cpaws_findings.md`의 §A/B/C/D/E 구조화된
> 발견을 토대로 전략적 해석을 더한 문서.

## 0. 목차

1. [요약](#1-요약)
2. [정량 개요](#2-정량-개요)
3. [CPaws 고유 가치 — 6 surfaces](#3-cpaws-고유-가치)
4. [Anthropic 레벨 게이트 — 양쪽 모두 거부 6 surfaces](#4-anthropic-레벨-게이트)
5. [행동 비대칭 — 같은 표면, 다른 런타임](#5-행동-비대칭)
6. [카테고리별 disagreement 집중도](#6-카테고리별-disagreement)
7. [운영 차원 — 인증, tier, SDK](#7-운영-차원)
8. [토큰 경제 및 비용 함의](#8-토큰-경제)
9. [Provider 선택 프레임워크](#9-provider-선택-프레임워크)
10. [이 매트릭스가 측정하지 *않는* 것](#10-매트릭스가-측정하지-않는-것)
11. [거시적 시사](#11-거시적-시사)
12. [워크로드별 권장](#12-워크로드별-권장)

---

## 1. 요약

2026-05-20 매트릭스는 4 cells (2 provider × 2 모델) 에서 57개 contract
probe 를 실측. 핵심:

- **핵심 Messages API 표면 (≈75%) 에서 양쪽이 동일하게 동작** — 기본
  생성, 스트리밍, tools, citations, documents, vision, multilingual
  모두 Bedrock 과 CPaws 에서 같음.
- **CPaws 가 Bedrock 이 거부하는 6 표면을 추가 제공** — count_tokens,
  server tools (web_search/web_fetch/code_execution), Opus 4.7 의 strict
  tool use, Opus 4.7 의 structured outputs, Anthropic-direct 엔드포인트
  (`messages.batches`, `models.list`), extended cache TTL beta 헤더.
- **6 표면은 Anthropic 자체가 게이팅** — 양쪽 ⛔. provider 를 바꿔도
  풀리지 *않음* (computer_use, tool_search, compaction beta, Opus 4.7
  assistant_prefill, sampling 파라미터 deprecation, Opus 4.7
  `thinking.enabled_with_effort`).
- **공유 표면에서 2 개의 미묘한 행동 비대칭** — `cache_ttl_1h` 두번째
  호출의 캐시 bucket 할당이 다름, 짧은 응답의 스트리밍 chunking 차이.
- **CPaws Tier 1 워크스페이스에는 30k input TPM 한도** — 단일 큰 요청
  이 그 한도를 초과하면 retry 가 풀지 못하는 429. PDF / 1M context
  probe 가 `cpaws/sonnet-4-6` 에서 이 때문에 실패 (contract 아님).

**TL;DR**: CPaws 는 Messages API 표면의 *superset* (Bedrock 대비 6 개
추가) 이고 공유 표면 런타임 동작은 *거의 동일* (측정 가능하지만 미세한
차이 2개). 둘의 선택은 *능력 자체*가 아니라 *운영 요인* (인증, 청구,
tier) 에 달려있음.

---

## 2. 정량 개요

### 2.1 셀별 합계

| Cell | 🟢 Supported | ⛔ Rejected (contract) | ❌ Fail | Total |
|---|---:|---:|---:|---:|
| `bedrock/opus-4-7` | 45 | 12 | 0 | 57 |
| `bedrock/sonnet-4-6` | 48 | 9 | 0 | 57 |
| `cpaws/opus-4-7` | 47 | 6 | 4 | 57 |
| `cpaws/sonnet-4-6` | 44 | 5 | 8 | 57 |

### 2.2 실효 coverage (❌ 분류 후)

probe 어서션이 Bedrock contract 모양으로 작성되어 있어 raw 매트릭스는
CPaws 의 coverage 를 *과소* 표시. 각 매트릭스의 MANIFEST.md 는 ❌ 를
3 buckets 로 재분류:

| Cell | Raw 🟢 | + ❌-as-🟢 (contract divergence 포착) | − Tier 1 RL ❌ | 실효 coverage |
|---|---:|---:|---:|---:|
| `bedrock/opus-4-7` | 45 | 0 | 0 | 45/57 = 79% |
| `bedrock/sonnet-4-6` | 48 | 0 | 0 | 48/57 = 84% |
| `cpaws/opus-4-7` | 47 | +3 | 0 | **50/57 = 88%** |
| `cpaws/sonnet-4-6` | 44 | +3 | 3 개는 RL, contract 아님 | **47/57 = 82%** (RL 제외 시 47/54 = 87%) |

**해석**: CPaws 는 측정된 표면의 *더 많은* 부분을 지원. "❌ 가 많으니
더 나쁘다" 는 시각적 인상은 잘못. CPaws 에서 ❌ 인 probe 는 대부분
*CPaws 가 Bedrock 이 하지 않는 것을 한다는 신호* — probe 의 통과 조건이
Bedrock 거부를 가정.

### 2.3 Cross-provider divergence 개수

11 개 unique 테스트에서 16 개 (test, model) 짝이 양 provider 에서
다름:

```
unsupported       6 divergent 짝 / 카테고리 내 5 probes
caching           2 divergent / 8 probes
token_counting    2 divergent / 1 probe  (두 모델 모두)
documents         2 divergent / 2 probes (sonnet 에서 Tier 1 RL)
messages          1 divergent / 11 probes
tools             1 divergent / 11 probes
context           1 divergent / 2 probes
streaming         1 divergent / 5 probes
```

**관찰**: divergence 가 `unsupported/`, `caching/`, `token_counting/`,
`documents/` 에 집중. 이 4 개 카테고리 (admin 형 기능, 캐시 메커니즘,
토큰 introspection, 문서 처리) 가 거의 모든 cross-provider 결정의
원인. `messages`, `tools`, `multilingual`, `vision`, `citations` 5 개
"일상 API" 는 수렴.

---

## 3. CPaws 고유 가치

아래 6 표면은 Bedrock 에서 FAIL, CPaws 에서 작동. "CPaws 를 delivery
채널로 추가하는 이유" 의 *구체적* 답.

### 3.1 `messages.count_tokens`

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/token_counting/count_tokens.py` | ⛔ rejected | 🟢 input_tokens 카운트 반환 |

**의미**: `count_tokens` 없이는 요청 제출 *전* 토큰 사용량 추정 불가.
근사 (tiktoken 등) 는 Anthropic 의 실제 토크나이저와 일치하지 않음.
CPaws 는 canonical 답 — 다음 용도에 유용:
- 제출 전 비용 추정
- Sliding-window 프롬프트 구성
- Cache-key 엔지니어링 (정확한 토큰 경계 파악)

### 3.2 Server tools — web_search / web_fetch / code_execution

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/unsupported/server_tools.py` | ⛔ 3 tool type 모두 거부 | 🟢 3 모두 수락 *및 실행* |

**기능 검증 (`cpaws_findings.md §A.6`, 2026-05-12)**:
- `web_search` 쿼리 "2025년 노벨 물리학상 수상자" → 실제 수상자 반환
  (John Clarke, Michel H. Devoret, John M. Martinis). 토큰: 20,394
  input + 880 output.
- `web_fetch` URL `https://www.anthropic.com` → canonical URL +
  meta-description 포함한 실제 페이지 반환. 토큰: 8,439 input + 108
  output.
- 결과는 `encrypted_content` 블록 (모델만 복호화 가능).

**의미**: 모델 자신의 turn 안에서 액션 수행 가능 — 외부 오케스트레이션
불필요. Bedrock 대안은 클라이언트 측 tool 구현 + tool_use_id 로 결과
라우팅, 라운드트립 2배 + 평문 노출.

### 3.3 Opus 4.7 의 strict tool use (`strict_tool_use=True`)

| Probe | Bedrock opus-4-7 | CPaws opus-4-7 |
|---|---|---|
| `probes/tools/strict_tool_use.py` | ⛔ rejected | 🟢 supported |

**메모**: Sonnet 4.6 은 양 provider 에서 모두 지원 — divergence 는
Opus 4.7 한정. Bedrock 의 Opus 4.7 strict tool use 권장 경로는 Mantle
엔드포인트 (이 suite scope 밖).

**의미**: Strict tool use 는 tool 호출 시 JSON 인자가 선언된 schema 와
정확히 일치 보장 → "잘못된 인자로 함수 호출됨" 실패 모드 제거.

### 3.4 Opus 4.7 의 structured outputs (`output_config.format`)

| Probe | Bedrock opus-4-7 | CPaws opus-4-7 |
|---|---|---|
| `probes/messages/structured_outputs.py` | ⛔ rejected | 🟢 schema 준수 JSON 반환 |

3.3 과 같은 패턴 — sonnet 은 양쪽 작동, opus-4-7 만 divergence. 런타임
contract 는 "응답이 선언된 JSON schema 를 엄격히 준수". 없으면
`try/except json.JSONDecodeError` + 재프롬프트 사이클 필요.

### 3.5 Anthropic-direct 엔드포인트

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/unsupported/endpoints_absent.py` `messages.batches` | ⛔ attribute 부재 | 🟢 호출 가능 |
| `probes/unsupported/endpoints_absent.py` `models.list()` | ⛔ attribute 부재 | 🟢 6 모델 반환 (2026-05-20 검증) |

**CPaws `models.list()` 출력** (2026-05-20):
```
claude-opus-4-7
claude-sonnet-4-6
claude-opus-4-6
claude-opus-4-5-20251101
claude-haiku-4-5-20251001
claude-sonnet-4-5-20250929
```

**의미**: 동적 모델 발견 (모델 ID 하드코딩 불필요), 고-처리량 오프라인
처리용 batch 제출, admin 형 흐름이 CPaws 에 가용. Bedrock 동등 기능은
`boto3 bedrock` (별도 API) 으로 가능하지 `anthropic` SDK 로는 안 됨.

### 3.6 `extended-cache-ttl-2025-04-11` beta header

| Probe | Bedrock | CPaws |
|---|---|---|
| `probes/caching/extended_ttl_header_rejected.py` | ⛔ "invalid beta flag" | 🟢 헤더 수락 |

**메모**: 2026-05-20 매트릭스에서는 양쪽 ⛔ 로 표시 (테스트의
contract-divergent 인코딩 때문). 근본 동작은 2026-05-12 와 동일.

### 3.7 모델-tier 수렴 패턴

§3.3 과 §3.4 에서 sonnet-4-6 은 Bedrock 에서도 CPaws 와 동일 의미로
수렴. 가설 3가지:

1. **차등 출시**: Anthropic 가 sonnet 에 먼저 push, opus 는 별도 케이던스
2. **Opus 4.7 특별 정책**: Opus 4.7 이 Bedrock 에서 다른 엔드포인트 그룹
   (Mantle) 으로 라우트
3. **Beta 기능 졸업**: 처음엔 CPaws 전용이었던 기능이 성숙하면 모든
   provider 로 졸업

함의: **Bedrock 에서 opus-4-7 → sonnet-4-6 으로 옮기면 §A 6 표면 중
2 개가 자동 해소** — provider 변경 없이도.

---

## 4. Anthropic 레벨 게이트

양 provider 가 모두 거부하는 11 개 (test, model) 짝. 5 개 unique 표면에
매핑. Bedrock → CPaws 이동으로 풀리지 *않음*.

| 표면 | 모델 | 이유 | 우회 가능? |
|---|---|---|---|
| `computer_use_20250124` | 양쪽 | Anthropic 가 desktop 자동화 게이팅 | No |
| `tool_search_*` | 양쪽 | 별도 product 채널, 일반 가용 아님 | No |
| Opus 4.7 의 `assistant_prefill` (응답 prefix) | opus-4-7 | Opus 4.7 family 글로벌 deprecation | No |
| Sampling params (`temperature`/`top_p`/`top_k`) deprecation | Opus 4.7 두 모델 | 글로벌 deprecation | No |
| `thinking.enabled_with_effort` | Opus 4.7 만 | 글로벌 `adaptive` 로 마이그레이션 | No |

### 4.1 §B 를 모를 때의 비용

"X 얻으려고 Bedrock → CPaws 이동" 검토하는 팀은 X 를 §B 와 먼저 대조해야
함. 매트릭스가 깨끗하게 보여주지만, 양쪽 provider 에서 실행해야 검출
가능. 단일-provider 매트릭스라면 이 거부들을 Bedrock-특이 라고 잘못
귀속할 것.

### 4.2 Opus 4.7 sampling deprecation 강조 가치

3 표면이 양쪽 provider 에서 Opus 4.7 한정 ⛔:
- `assistant_prefill`
- `sampling_params_deprecated`
- `thinking.enabled_with_effort`

이는 **Opus 4.7 이 Opus 4.6/Sonnet 4.6 보다 좁은 contract 표면**임을
시사. 이 knob 들에 의존하는 코드베이스는 **provider 무관, Opus 4.6 유지
또는 Sonnet 4.6 이전**.

---

## 5. 행동 비대칭

양쪽 provider 에서 수락되지만 **런타임 동작이 다른** 표면. 가장 위험한
범주 — Bedrock 에서 잘 돌던 코드가 CPaws 에서 (또는 그 반대로) 미묘하게
다른 행동을 보이면서 명확한 에러 없이 작동.

### 5.1 `cache_ttl_1h` — 두 번째 호출의 캐시 bucket 할당

**Bedrock (두 모델, ap-northeast-2)**:
```
첫 호출:    cache_creation.ephemeral_1h_input_tokens = 15,025
            cache_read_input_tokens                   = 0
두 번째:    cache_creation.ephemeral_1h_input_tokens = 0
            cache_read_input_tokens                   = 15,025
            ← 깨끗: 1h bucket read 만, 신규 write 0
```

**CPaws (두 모델, us-east-2)**:
```
첫 호출:    cache_creation.ephemeral_1h_input_tokens = 15,021
            cache_read_input_tokens                   = 0
두 번째:    cache_creation.ephemeral_5m_input_tokens = 5-8
            cache_read_input_tokens                   = 15,021
            ← 1h read 정상 작동, 그러나 5m bucket 에 5-8 토큰 추가 write
```

**재현성**: 이번 2026-05-20 실행에서 `cpaws/opus-4-7` 과
`cpaws/sonnet-4-6` 양쪽 us-east-2 에서 확인 — region 이나 모델이 단일
원인 아님. 2026-05-12 ap-northeast-2 에서 최초 문서화.

**비용 함의**:
- 1회성 캐시 read: 무시 가능 (두 번째 호출당 5-8 토큰).
- 지속 워크로드 (시스템 프롬프트 캐시 시간당 1000번 재사용): 시간당
  5,000-8,000 추가 청구 토큰, *기대되는* cache_read 청구 *위에* 추가.
- 패턴: CPaws 의 모든 "cache hit" 에 작은 강제 write 세금.

**추정 원인** (미검증 가설): CPaws 캐시 레이어가 두 번째 호출의 non-prefix
부분을 자체 캐시 엔트리가 필요한 새 prefix 로 처리, Bedrock 은 read-only
delta 로 식별.

**미해결 가설** (`cpaws_findings.md §C.1`):
- CPaws 인프라의 캐시 propagation 지연
- 1h bucket 이 5m bucket 과 다른 storage 계층에서 서빙
- region 특이 (2026-05-20 에서 us-east-2 가설 배제)

### 5.2 짧은 응답의 스트리밍 chunking granularity

**Bedrock**: 짧은 프롬프트 "1, 2, 3, 4, 5 까지 응답" 이 다수의
`RawContentBlockDeltaEvent` 발생 — 단어당 또는 몇 토큰당 1개.

**CPaws**: 같은 프롬프트가 정확히 **1 개** delta 이벤트 (전체 텍스트가
단일 chunk):
```
event_kinds: RawMessageStartEvent, RawContentBlockStartEvent,
             RawContentBlockDeltaEvent (×1), RawMessageDeltaEvent,
             ParsedContentBlockStopEvent, ParsedMessageStopEvent,
             TextEvent
stop_reason: end_turn
preview: "1, 2, 3, 4, 5"
delta_count: 1
```

**UX 함의**:
- 최종 텍스트와 `stop_reason` 은 Bedrock 과 동일.
- Progressive UI 렌더링 (문자별 애니메이션, 단어별 reveal) 은 CPaws 에서
  짧은 응답이 *부드럽게 흘러나오지 않고 점프*.
- 긴 응답은 CPaws 에서도 정상 chunking 예상 (미측정, `cpaws_findings.md
  §G` 후속 항목).
- *인프라 레벨 버퍼링*이지 모델 행동 차이 아님.

**검출**: stream-aware probe 에서 `delta_count > N` 핀.

---

## 6. 카테고리별 disagreement

16 개 cross-provider (test, model) divergence 가 카테고리에 매핑되는
형태가 provider 선택 영향 위치를 보여줌:

```
unsupported     ████████ 6  (probe 도메인: cross-provider 차이)
caching         ██       2  (cache_ttl_1h 두 모델)
token_counting  ██       2  (count_tokens 두 모델)
documents       ██       2  (sonnet Tier 1 RL — contract 아님)
messages        █        1  (structured_outputs opus-4-7)
tools           █        1  (strict_tool_use opus-4-7)
context         █        1  (context_1m_beta sonnet — Tier 1 RL)
streaming       █        1  (delta count sonnet)
```

**카테고리별 해석**:

| 카테고리 | Divergence 비율 | 해석 |
|---|---|---|
| `unsupported/` | 6/5 (>100% — 멀티 모델) | 이 카테고리 자체가 cross-provider 차이를 인코딩하기 위해 존재. 의도대로 작동. |
| `caching/` | 2/8 = 25% | provider 선택이 캐시 동작에 의미 있게 영향 |
| `token_counting/` | 2/1 = 200% (두 모델) | 단일 probe 지만 CPaws 의 unique offer |
| `documents/` | 2/2 = 100% (sonnet RL) | contract 아님 — heavy probe 의 Tier 1 한도 |
| `messages/` | 1/11 = 9% | 91% 수렴 — 핵심 API 는 portable |
| `tools/` | 1/11 = 9% | 91% 수렴 |
| `multilingual/` | 0/2 = 0% | 동일 |
| `vision/` | 0/2 = 0% | 동일 |
| `citations/` | 0/2 = 0% | 동일 |
| `thinking/` | 0/5 = 0% | 동일 |

**함의**: `messages`, `tools`, `multilingual`, `vision`, `citations`,
`thinking`, `client`, `streaming` 카테고리 코드는 **provider 간 거의
0 적응으로 portable**. `unsupported`, `caching`, `token_counting`,
`documents` 경계에 닿는 코드는 provider-aware 경로 필요.

---

## 7. 운영 차원

### 7.1 인증

| Dimension | Bedrock | CPaws |
|---|---|---|
| 주 인증 | AWS Bearer (`AWS_BEARER_TOKEN_BEDROCK`) | Workspace API key (`x-api-key` + `anthropic-workspace-id` 헤더) |
| 키 형식 | `ABSK` prefix, base64-encoded | `AEAA` prefix, base64-encoded (유사 모양) |
| SDK 클래스 | `AnthropicBedrock`, `AsyncAnthropicBedrock` | `AnthropicAWS`, `AsyncAnthropicAWS` |
| IAM 통합 | ✅ Native (Bedrock SigV4 + bearer token 지원) | ⚠ SDK 가 SigV4 경로 지원하지만 workspace key 가 문서화 기본 |
| 엔드포인트 형식 | `bedrock-runtime.<region>.amazonaws.com` | `aws-external-anthropic.<region>.api.aws` |
| 로테이션 | AWS 콘솔, IAM 정책 | Anthropic 콘솔 |
| 감사 추적 | CloudTrail (DataPlane 이벤트) | (CPaws 별도 — CloudTrail 아님) |

### 7.2 Rate limit / tier 모델

| Aspect | Bedrock | CPaws |
|---|---|---|
| 한도 메커니즘 | region 별 AWS service quota, 모델별 | Anthropic tier 시스템 (Tier 1-4) workspace 단위 |
| Tier 1 input TPM | (AWS 서비스 quota — 일반적으로 더 관대) | **30,000 input 토큰/분** (2026-05-20 측정) |
| Tier 1 output TPM | (Bedrock 모델 quota) | Tier 의존 |
| 단일 요청 크기 한도 | 모델 컨텍스트 윈도우만 제한 | 단일 요청이 분당 budget 초과 → 즉시 429 |
| Burst tolerance | ✅ region-wide pool | ⚠ workspace 단위 |
| 529 Overloaded | 범용 호출에서는 드물게 | 이번 실행에서 Haiku 4.5 에 지속 관찰 |
| 재시도 동작 | SDK 기본 2회 재시도 | 10 으로 상향 (`providers/cpaws.py`, env `CPAWS_MAX_RETRIES`) |

**Tier 1 의 30k 한도 함의**:
- 단일 PDF probe (~32k input 토큰) 가 분당 budget 전체 차지, 429 반환,
  backoff 로 재시도해도 여전히 초과 가능.
- 호출당 >5k input 토큰 워크로드는 Tier 1 으로 매트릭스 형 직렬 sweep
  불가.
- Tier 2+ 업그레이드 (Anthropic 콘솔에서 요청) 또는 입력 분할.

### 7.3 SDK / API 표면

| Endpoint | Bedrock | CPaws |
|---|---|---|
| `messages.create` | ✅ | ✅ |
| `messages.stream` | ✅ | ✅ (5.2 chunking 주의) |
| `messages.count_tokens` | ⛔ | ✅ |
| `messages.batches.*` | ⛔ attribute_absent | ✅ |
| `models.list` | ⛔ attribute_absent | ✅ |
| `files.*` | ⛔ attribute_absent | ⛔ **CPaws 도 absent** — SDK 버전 의존 (§G.5) |
| `admin.*` | (미테스트) | (미테스트) |
| Async 동등 | `AsyncAnthropicBedrock` | `AsyncAnthropicAWS` |

### 7.4 청구

| Aspect | Bedrock | CPaws |
|---|---|---|
| 청구 경로 | AWS 계정 (Bedrock 서비스) | AWS Marketplace (Claude on AWS) |
| 토큰 가격 | Bedrock list pricing | Anthropic list pricing × Marketplace markup (현재 확인 필요) |
| 캐시 할인 | ✅ 문서화 | ✅ 문서화 |
| Cross-region 비용 | Cross-region 전송 요금 발생 가능 | (Marketplace 계약별 확인) |

---

## 8. 토큰 경제

### 8.1 2026-05-20 실행당 비용 proxy

per-cell 토큰 accumulator 출력 (셀당 57 probe 합계 — failure rate 가 총
API 호출 수에 영향 미치므로 셀간 직접 비교 불가):

| Cell | 실행된 probe | 근사 input billable (k) |
|---|---:|---:|
| `bedrock/opus-4-7` | 57/57 PASS, 전체 토큰 소모 | ~570k (2026-05-12 비교 가능 baseline 기준) |
| `bedrock/sonnet-4-6` | 57/57 PASS | ~570k |
| `cpaws/opus-4-7` | 57 시도, 53 안착, 4 ❌ | ~530k |
| `cpaws/sonnet-4-6` | 57 시도, 다수가 429 후 재시도 | (rate-limited probe 의 SDK 재시도로 증가) |

**주의**: 이 매트릭스는 coverage probe 이지 벤치마크 아님. 토큰 비용은
가장 큰 probe (PDF, context_1m) 가 지배 → 셀별 합계는 *상한* 지표만.

### 8.2 §5.1 의 캐시 비용 비대칭

15k 토큰 cached prefix 를 시간당 1,000번 재사용하는 가상 워크로드:

| Provider | hit 당 billable | 시간당 1000 hits billable |
|---|---:|---:|
| Bedrock | ~0 cache_create + 15,025 cache_read | 15,025,000 cache_read 토큰 |
| CPaws | ~5-8 cache_create (5m bucket) + 15,021 cache_read | 15,021,000 cache_read + 5,000-8,000 cache_create |

**연간 영향**: 고-빈도 cached-prefix 워크로드의 경우 연간 ~50-70 백만
cache_create 토큰 추가. 대표적인 $0.30/1M-tok cache_create 가격에서
**연 ~$15-25 추가** — 절대 금액은 작지만 체계적인 세금.

### 8.3 "공짜" 기능에도 비용

CPaws 의 6 unique 표면 (§3) 은 API 경제 측면에서 무료 아님:
- `count_tokens` 호출 billed (작음)
- Server tools (`web_search` 가 20k input + 880 output 반환; 사용당)
- Batches API 는 자체 billing 모델 (일반적으로 할인, 확인 필요)

요점: §3 표면은 *능력*을 푸는데, 사용 빈도가 provider 전환 자체보다
지출에 더 영향 미침.

---

## 9. Provider 선택 프레임워크

§3-§8 종합한 결정 rubric:

### 9.1 Bedrock 을 선택하는 경우

- AWS-native 통합이 load-bearing (VPC endpoint, PrivateLink, 서비스 간
  인증용 IAM role)
- Compliance / data residency 가 CPaws Marketplace 에 아직 없는
  AWS region 요구
- 기존 AWS Cost Explorer / Cost & Usage Report 통합
- 단일 요청 페이로드 큼 (PDF 처리, 1M context probe) — Tier 1 한도 제한적
- CloudTrail API 호출 감사 추적 원함
- *Mantle endpoint* 기능 필요 (이 매트릭스 scope 밖)

### 9.2 CPaws 를 선택하는 경우

- 비용 미리보기 / 윈도잉 위해 `count_tokens` 필요
- Server tools (`web_search`, `web_fetch`, `code_execution`) 필요
- Opus 4.7 에서 `strict_tool_use` 또는 `structured_outputs` 필요
  (그리고 Mantle 미사용)
- 고-처리량 오프라인 처리용 batch API 필요
- canonical 1P Anthropic 행동 원함 (AWS 청구 유지하면서 direct
  Anthropic API 에 가장 가까운 환경)
- `models.list()` 통한 동적 모델 발견 필요

### 9.3 양쪽 모두 사용하는 경우

- 워크로드별로 다른 요구 (e.g. 대화형 UI 는 Bedrock, batch enrichment 는
  CPaws)
- Provider 행동 비교 자체가 요구사항 (이 매트릭스)
- Failover 또는 capacity 다양화

### 9.4 어느 경로도 풀지 못함

- `computer_use_20250124` (Anthropic 게이팅)
- `tool_search_*` (별도 채널)
- Opus 4.7 의 `assistant_prefill`, sampling 파라미터,
  `thinking.enabled_with_effort` (글로벌 deprecation)
- `compaction-2025-09-17` beta (flag 미릴리스)

이들에 대한 답은 "기다림" (deprecation 번복 가능성 낮음) 또는 "다른
모델 family 사용" (Sonnet 4.6 이 일부 유지).

---

## 10. 매트릭스가 측정하지 *않는* 것

정직한 분석을 위해 한계 명시. 2026-05-20 매트릭스가 측정 *안 한* 것:

1. **Batches workflow** — `client.messages.batches.*` attribute *존재*만
   테스트. batch 제출 → 실행 → 회수 흐름 미실행. CPaws 가 mid-flow 에서
   다르게 동작할 수 있음.
2. **Files API** — 양 provider 가 `client.files.*` 에 대해
   `attribute_absent` 표시. **SDK 버전 의존** 가능성 큼, server-side
   부재 아닐 수 있음. `anthropic` 패키지 업그레이드 후 재시험 필요
   (`cpaws_findings.md §G.5`).
3. **Admin API** — `client.admin.*` (조직/워크스페이스 관리) 이 suite 에
   없음.
4. **가격 차이** — Bedrock vs CPaws 의 동일 토큰 소비에 대한 USD 레벨
   비용 비교 없음.
5. **Latency** — 요청-응답 wall-clock 시간 벤치마크 안 됨. 이 매트릭스의
   probe 별 `elapsed_s` 값은 retry-after sleep 포함 → clean latency
   아님.
6. **장기 안정성** — 1일 스냅샷. CPaws 의 Haiku 4.5 에서 관찰된
   Anthropic capacity 이벤트 (529 Overloaded) 특성화 위해 다일 샘플링
   필요.
7. **Cross-region 동작** — CPaws 는 `us-east-2`, Bedrock 은
   `ap-northeast-2` 에서 테스트. 양쪽 동일 region 은 이번 실행에서
   측정 안 됨 (2026-05-12 baseline).
8. **고-동시성 워크로드** — 매트릭스는 직렬. 특히 Tier 1 한도 아래
   동시 요청 동작은 다를 수 있음.
9. **긴 응답의 스트리밍 동작** — §5.2 짧은 응답 chunking 측정, 긴 응답
   chunking 은 probe 코드에서 추론하지만 구체 비교 안 됨.
10. **PrivateLink / VPC endpoint 경로** — Bedrock 은 지원, CPaws 의
    네트워크 경로 특성은 미특성화.
11. **CPaws 의 Haiku 4.5 baseline** — 시도했으나 지속 529 차단. `MODEL_ALIASES`
    에서 제외. Tier 1 capacity 회복 필요 (`cpaws_findings.md §G.6`).
12. **Mantle endpoint** — `bedrock-mantle.<region>.api.aws` 는 명시적으로
    이 suite scope 밖 (project memory: "Mantle 은 opt-in, 기본 아님").

---

## 11. 거시적 시사

### 11.1 두 provider 는 경쟁이 아니라 보완

핵심 Messages API 표면의 75% 수렴은 CPaws 가 "다른 LLM 플랫폼" 이
아니라 "같은 Anthropic 모델을 다른 운영 envelope 으로 제공" 함을 의미.
경쟁 frame 은 잘못. *포트폴리오* frame 이 옳음:
- Bedrock: AWS-shaped Anthropic
- CPaws: Anthropic-shaped Anthropic delivered via AWS

같은 모델, 같은 생성 품질, 같은 SLA (Anthropic 측). 다른 ergonomics, 다른
기능 표면, 다른 인증.

### 11.2 "1P 마이그레이션" 의사결정에 정량화된 답 확보

매트릭스 이전 질문 "1P (직접 Anthropic API) 로 이동할까?" 가 CPaws 에서
더 작은 질문이 됨: "§A 6 표면 중 필요한 것 있는가?". 매트릭스가 binary
답 제공:

- **있다면**: CPaws 로 이동 (완전한 1P direct 마이그레이션보다 저렴 —
  같은 AWS 청구, 같은 VPC, 같은 compliance 표면).
- **없다면**: Bedrock 유지 (운영 단순성, 넓은 region 가용성, 성숙한
  CloudTrail).

매트릭스가 "뭔가 놓치는 거 아닐까?" 의 FUD 제거. 답: 6 개 특정 표면,
이름으로 나열됨.

### 11.3 테스트 suite 설계가 portable 인사이트

매트릭스의 *meta* 가치: 어느 팀이든 자기 워크스페이스 자격증명으로
실행해 자기 컨텍스트에서 같은 발견 검증 가능한 portable Python harness.
구체적으로:

- `probes/` 는 Python 라이브러리로 import 가능
- `scripts/rerun_cells.py` 가 커스텀 pacing 으로 1 cell 재생성
- `scripts/snapshot_matrix.py` 가 dated baseline 생성

팀들이 "내 워크스페이스 tier 한도가 영향을 주는가?", "내 region 이
같은 동작을 보이는가?", "Anthropic 이 이번 주에 뭐 바꿨나?" 를 support
에스컬레이션 대신 경험적으로 답할 수 있음.

### 11.4 Probe 어서션 모양이 leverage point

§10 과 §6 의 반복 교훈: 매트릭스 ❌ 개수가 provider disagreement 를
과대 표시 — probe 어서션이 단일 provider 의 contract 를 인코딩하기
때문. MANIFEST 의 `_failure_caveats` 분류기가 *해석 레이어* — raw
매트릭스를 실제 인사이트로 변환.

**함의**: 미래 probe 리팩토링은 `info.contract = "supported_on_X" /
"rejected_on_Y"` 패턴 (`test_sampling_deprecated` 패턴) 으로 contract
인코딩 — runner 의 분류기를 single source of truth 로 만들고 "❌
인데 사실 🟢" 불일치 제거.

---

## 12. 워크로드별 권장

| 워크로드 | 권장 provider | 사유 |
|---|---|---|
| 대화형 chat UI (실시간 SSE 렌더링, 짧은 응답) | **Bedrock** | §5.2 스트리밍 chunking 이 progressive UI 에 유리 |
| Batch 문서 처리 (PDF, OCR 파이프라인) | **Bedrock** (단일 요청) 또는 **CPaws Tier 2+** (batches API) | Tier 1 한도가 CPaws 의 단일-PDF probe 차단 |
| 비용 민감 프롬프트 엔지니어링 (캐시 + 토큰 카운팅) | **CPaws** | `count_tokens` 가 빡빡한 budgeting 가능 |
| Web tools 가진 agentic 워크플로우 | **CPaws** | Server tools (`web_search`, `web_fetch`, `code_execution`) native 실행 |
| 구조화된 데이터 추출 (JSON schema) | **CPaws** for Opus 4.7; Sonnet 4.6 은 양쪽 | `output_config.format` 이 opus-4-7 에서 CPaws 만 가능 |
| 고-처리량 async / 오프라인 | **CPaws** (`messages.batches.*`) | CPaws 에서만 SDK 통해 가용 |
| Compliance heavy (CloudTrail, IAM 정책, PrivateLink) | **Bedrock** | Native AWS 통합 |
| Multi-region active-active 페일오버 | **양쪽** (서로 백업) | 다양화 |
| Opus 4.7 의 strict tool calling | **CPaws** | Bedrock 은 Mantle 필요 (여기 scope 밖) |
| Tier 1 워크스페이스에서 long-context (>200k input 토큰) | **Bedrock** | 단일-호출 페이로드가 CPaws Tier 1 분당 budget 초과 |
| 1h TTL prefix 재사용이 많은 cache-heavy | **Bedrock** | §5.1 — 두 번째 호출 read 에 5m bucket 세금 없음 |

---

## 13. 참조

- `results/runs/2026-05-20/matrix.{json,md}` — 원본 매트릭스 데이터
- `results/runs/2026-05-20/MANIFEST.md` — failure 분류
- `results/runs/2026-05-20/bedrock.md` / `cpaws.md` — provider 별 뷰
- `results/cpaws_findings.md` — §A/B/C/D/E 구조화된 발견 (baseline
  2026-05-12, refresh 2026-05-20)
- `results/docs_vs_reality.md` — Anthropic 공식 문서 vs 실측 contract
- `results/prompt_caching_verified.md` — cache contract 참조, §P-1
  cold-start salt 증거
- `probes/` — import 가능한 contract probe 라이브러리
- `config.py` — `MODEL_ALIASES`, `BEDROCK_UNSUPPORTED`
- `providers/cpaws.py` — `max_retries=10` Tier 1 hardening

**이 분석의 스냅샷 identity**: `git 0c98a88` on `main`, 2026-05-20 UTC.





