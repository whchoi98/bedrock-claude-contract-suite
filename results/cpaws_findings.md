# Claude Platform on AWS — Contract Findings (vs Bedrock)

> Empirical comparison between Amazon Bedrock Invoke API and
> Claude Platform on AWS (`aws-external-anthropic.{region}.api.aws`)
> on identical contract tests. First baseline run: **2026-05-12**.
>
> Bilingual document — English first, 한국어 below.

## Scope · Methodology

- **Date**: 2026-05-12
- **Model**: `claude-opus-4-7` (alias used across both providers)
  - Bedrock concrete ID: `global.anthropic.claude-opus-4-7`
  - CPaws concrete ID:   `claude-opus-4-7`
- **Region**: `ap-northeast-2` (both providers)
- **CPaws auth**: workspace API key (`ANTHROPIC_AWS_API_KEY` + `anthropic-workspace-id` header)
- **Bedrock baseline**: `results/matrix-2026-05-04.md` (3-model matrix)
- **CPaws full sweep**: `results/latest.md` produced by
  `python3 run_all.py --providers cpaws` on 2026-05-12T22:31:58Z.
  Result: **51 / 57 passed**.

## §A. Features CPaws supports that Bedrock rejects

These six surfaces FAIL on Bedrock (`⛔ rejected`) but WORK on CPaws.
They are the primary cross-provider divergence — the empirical answer
to "what do I gain by adding CPaws as a target?".

| # | Surface | Bedrock | CPaws | Evidence |
|---|---------|---------|-------|----------|
| 1 | **`messages.count_tokens`** | ⛔ rejected | 🟢 supported | `tests/token_counting/test_count_tokens` — info.contract changes from `"rejected"` (bedrock) → `"supported"` (cpaws) |
| 2 | **`anthropic-beta: extended-cache-ttl-2025-04-11`** | ⛔ rejected | 🟢 accepted | `tests/caching/test_extended_ttl_header_rejected` — header accepted on CPaws (test contract supports both branches) |
| 3 | **Strict tool use** (`strict_tool_use=True`) | ⛔ rejected | 🟢 supported | `tests/tools/test_strict_tool_use` |
| 4 | **Structured outputs** (response strictly conforms to JSON schema) | ⛔ rejected | 🟢 supported | `tests/messages/test_structured_outputs` |
| 5 | **Anthropic-direct endpoints**: `client.messages.batches.*`, `client.models.list()` | ⛔ attribute_absent | 🟢 succeeded | `tests/unsupported/test_endpoints_absent` (probe failures = surfaces present) |
| 6 | **Server tools**: `web_search_20250305`, `web_fetch_20250910`, `code_execution_20250825` | ⛔ rejected | 🟢 all 3 accepted | `tests/unsupported/test_server_tools` |

### A.6 functional probe — server tools actually execute (not just accepted)

We confirmed `web_search` and `web_fetch` perform real actions, not just
accept the tool declaration silently.

**web_search** (query: "Who won the 2025 Nobel Prize in Physics?"):
```
server_tool_use → web_search { query: "2025 Nobel Prize in Physics winner" }
web_search_tool_result → (encrypted result blocks)
text → "The 2025 Nobel Prize in Physics was awarded jointly to
        John Clarke, Michel H. Devoret, and John M. Martinis..."
```
- Real laureates returned (factual match against 2025 Nobel announcement).
- Token usage: 20,394 input + 880 output.
- Search results delivered as `encrypted_content` (model-only decryption).

**web_fetch** (URL: `https://www.anthropic.com`):
```
server_tool_use → web_fetch { url: "https://www.anthropic.com" }
web_fetch_tool_result → WebFetchBlock(content=DocumentBlock(
    citations=None,
    source=PlainTextSource(data="---\ncanonical: ...\nmeta-description: ...")))
text → "The page title is: 'Home \\ Anthropic'"
```
- Real page fetched with metadata (canonical URL, meta-description).
- Token usage: 8,439 input + 108 output.
- Result block compatible with citation API (DocumentBlock structure).

## §B. Surfaces rejected on BOTH providers (Anthropic-level gating, not Bedrock-only)

Initial assumption was "Bedrock rejects, CPaws accepts" for everything in
`BEDROCK_UNSUPPORTED`. Empirically, six surfaces are gated at the API
level by Anthropic itself, regardless of provider. Migrating workloads to
CPaws does NOT unlock these.

| Surface | Bedrock | CPaws | Note |
|---------|---------|-------|------|
| `computer_use_20250124` tool type | ⛔ rejected | ⛔ rejected | Anthropic gates this — both providers reject. Test `test_computer_use_rejected` passes on both. |
| `tool_search_*` tool type | ⛔ rejected | ⛔ rejected | Likely a separate product channel. |
| `anthropic-beta: compaction-2025-09-17` | ⛔ rejected | ⛔ rejected (different wording — see §D) | beta flag not released. |
| Assistant prefill on Opus 4.7 | ⛔ rejected | ⛔ rejected | Deprecation, not provider-specific. |
| Sampling params (`temperature`, `top_p`, `top_k`) on Opus 4.7 | ⛔ deprecated | ⛔ deprecated | Deprecation, not provider-specific. Opus 4.6 / Sonnet 4.6 still legacy-accept on both. |
| `thinking.enabled_with_effort` on Opus 4.7 | ⛔ rejected | ⛔ rejected | Migrated to `adaptive` on Opus 4.7 globally. |

## §C. Behavioral differences (same surface, different runtime behavior)

Surfaces accepted on both providers but exhibiting measurable runtime
differences. These are the most subtle findings and warrant ongoing
monitoring.

### C.1 — 1-hour cache: write succeeds, immediate read does not (CPaws)

Bedrock: `cache_control: {ttl: "1h"}` → first call creates 1h cache,
second call hits it (`cache_read_input_tokens > 0`). Verified in
`results/prompt_caching_verified.md` §P-1.

**CPaws (2026-05-12, opus-4-7, ap-northeast-2)**: First call populates
`ephemeral_1h_input_tokens = 15025` ✅. Second call with the same prefix
returns `cache_read_input_tokens = 0` ❌ and writes a fresh
`ephemeral_5m_input_tokens = 8`. The 1h cache write is *recorded* but
not *served back* to the immediate subsequent request.

Hypotheses (not yet investigated):
- Cache propagation delay in CPaws infrastructure.
- 1h bucket served from a different storage tier than 5m bucket.
- Region-specific behavior (only verified in `ap-northeast-2`).

Test: `tests/caching/test_ttl_1h` — currently FAILS on CPaws despite
the contract producing useful diagnostic data.

### C.2 — Streaming delta count of 1 (CPaws, short responses)

Bedrock streaming for short prompts (~"reply 1, 2, 3, 4, 5") produces
multiple `RawContentBlockDeltaEvent` events — typically one per word or
per few tokens. CPaws produced exactly **one** delta event for the same
prompt:
```
event_kinds: RawMessageStartEvent, RawContentBlockStartEvent,
             RawContentBlockDeltaEvent, RawMessageDeltaEvent,
             ParsedContentBlockStopEvent, ParsedMessageStopEvent,
             TextEvent
stop_reason: end_turn
preview: "1, 2, 3, 4, 5"
delta_count: 1
```

Final response text and `stop_reason` are correct; only the
*event chunking granularity* differs. May be infrastructure-specific
(CPaws buffering short responses) or SDK version difference. Verify
on longer responses before drawing contract conclusions.

Test: `tests/streaming/test_text_deltas` — currently FAILS on CPaws
because it asserts `delta_count > 1`.

## §D. Test brittleness uncovered (Bedrock-specific assertions)

Two tests authored for Bedrock-specific error wording fail on CPaws
even though the *semantic* contract is identical. Tracked for P4
follow-up:

| Test | Issue | Fix direction |
|------|-------|---------------|
| `compaction_beta_header_rejected_on_bedrock` | Asserts `"invalid beta flag"` substring. CPaws rejects with `"Unexpected value(s) compaction-2025-09-17 for the anthropic-beta header"`. Both reject, wording differs. | Make matcher OR over both patterns. |
| `async_client` | Hard-codes `AsyncAnthropicBedrock` import → demands `AWS_BEARER_TOKEN_BEDROCK` even on CPaws runs. | Make provider-aware: use `AsyncAnthropic` for CPaws. |

These are NOT contract findings — they are test-suite gaps surfaced by
running the suite against a second provider.

## §E. Token cost observations (CPaws, 2026-05-12 run)

Full 57-test sweep on `claude-opus-4-7`:

- Wall-clock: 187 seconds.
- API calls: 61.
- Input tokens: 284,650.
- Output tokens: 2,479.
- Cache create (5m): 99,426.
- Cache create (1h): 27,041 (works on CPaws despite §C.1).
- Cache read: 125,944.
- Total billable input: 537,061 tokens.

The 1h cache *write* (27k tokens) succeeds and is billed; the
*read-back* anomaly (§C.1) means downstream tests in the same run
re-write the cache instead of hitting it. Bill impact is small for
short-running matrices but compounds for longer sessions.

## §F. Updates applied to the suite from this run

- `tests/unsupported/test_server_tools.py` — added
  `web_fetch_20250910` alongside `web_search` and `code_execution`.
- `config.BEDROCK_UNSUPPORTED` — added `server_tool_web_fetch`.
- `config.BEDROCK_UNSUPPORTED` comment — annotated that `computer_use`
  is also rejected on CPaws (Anthropic-level gating, not Bedrock-only).

## §G. Follow-ups (not in this baseline)

1. **Bedrock × CPaws full matrix** — both providers × 3 models × 57 tests.
   Cross-provider differences section will surface §A items as label-diff
   rows automatically.
2. **Bedrock baseline for `web_fetch_20250910`** — current Bedrock baseline
   (2026-05-04) tested only `web_search` and `code_execution`. Need a
   Bedrock run with the updated `test_server_tools` to confirm `web_fetch`
   is rejected there.
3. **§C.1 cache 1h read deeper probe** — vary delay between first and
   second call, try same-region vs cross-region, observe `cache_read`
   over time.
4. **Provider-divergent contract encoding for §D tests** — apply the
   `test_sampling_deprecated` pattern (`info.contract = "rejected_on_X"
   vs "supported_on_Y"`) to `compaction_beta_header_rejected_on_bedrock`
   and `async_client`.
5. **Files API empirical check** — `client.files.*` is `attribute_absent`
   on both providers in this SDK version. Upgrade `anthropic` and re-test.

---

# Claude Platform on AWS — 컨트랙트 발견 (vs Bedrock)

> Amazon Bedrock Invoke API 와 Claude Platform on AWS
> (`aws-external-anthropic.{region}.api.aws`) 에 동일한 contract 테스트
> 모음을 돌려 얻은 실측 비교. 첫 baseline 실행: **2026-05-12**.

## 범위 · 방법

- **날짜**: 2026-05-12
- **모델**: `claude-opus-4-7` (두 provider에서 동일 alias 사용)
  - Bedrock 실제 ID: `global.anthropic.claude-opus-4-7`
  - CPaws 실제 ID:   `claude-opus-4-7`
- **리전**: `ap-northeast-2` (두 provider 동일)
- **CPaws 인증**: workspace API key (`ANTHROPIC_AWS_API_KEY` +
  `anthropic-workspace-id` 헤더)
- **Bedrock baseline**: `results/matrix-2026-05-04.md` (3-모델 매트릭스)
- **CPaws 전체 스위트**: `results/latest.md` —
  `python3 run_all.py --providers cpaws` 2026-05-12T22:31:58Z 실행 결과.
  **51 / 57 통과**.

## §A. CPaws 에서 새로 작동하는 기능 (Bedrock 거부 → CPaws 지원)

여섯 개 표면이 Bedrock 에서 `⛔ rejected` 인데 CPaws 에서는 작동.
"CPaws 를 추가 target 으로 둘 때 얻는 게 무엇인가" 의 실측 답변.

| # | 표면 | Bedrock | CPaws | 근거 테스트 |
|---|------|---------|-------|-------------|
| 1 | **`messages.count_tokens`** | ⛔ 거부 | 🟢 지원 | `tests/token_counting/test_count_tokens` — info.contract `"rejected"` → `"supported"` |
| 2 | **`anthropic-beta: extended-cache-ttl-2025-04-11`** | ⛔ 거부 | 🟢 수락 | `tests/caching/test_extended_ttl_header_rejected` |
| 3 | **Strict tool use** (`strict_tool_use=True`) | ⛔ 거부 | 🟢 지원 | `tests/tools/test_strict_tool_use` |
| 4 | **Structured outputs** (JSON schema 강제) | ⛔ 거부 | 🟢 지원 | `tests/messages/test_structured_outputs` |
| 5 | **Anthropic-direct 엔드포인트**: `client.messages.batches.*`, `client.models.list()` | ⛔ 속성 부재 | 🟢 호출 성공 | `tests/unsupported/test_endpoints_absent` |
| 6 | **Server tools**: `web_search_20250305`, `web_fetch_20250910`, `code_execution_20250825` | ⛔ 거부 | 🟢 셋 다 수락 | `tests/unsupported/test_server_tools` |

### A.6 기능 probe — server tool 이 실제로 *실행* 됨 (수락만 한 게 아님)

`web_search` 와 `web_fetch` 가 단순 수락이 아니라 **실제 액션 수행**을
검증.

**web_search** (쿼리: "2025년 노벨 물리학상 수상자"):
```
server_tool_use → web_search { query: "2025 Nobel Prize in Physics winner" }
web_search_tool_result → (암호화된 결과 블록)
text → "The 2025 Nobel Prize in Physics was awarded jointly to
        John Clarke, Michel H. Devoret, and John M. Martinis..."
```
- 실제 수상자 정확히 반환 (2025년 노벨 위원회 공식 발표와 일치).
- 토큰 사용: input 20,394 / output 880.
- 검색 결과는 `encrypted_content` 형태 (모델만 복호화 가능).

**web_fetch** (URL: `https://www.anthropic.com`):
```
server_tool_use → web_fetch { url: "https://www.anthropic.com" }
web_fetch_tool_result → WebFetchBlock(content=DocumentBlock(
    citations=None,
    source=PlainTextSource(data="---\ncanonical: ...\nmeta-description: ...")))
text → "The page title is: 'Home \\ Anthropic'"
```
- 실제 페이지 페치 + 메타데이터 (canonical URL, meta-description) 포함.
- 토큰 사용: input 8,439 / output 108.
- 결과 블록이 citation API 호환 구조 (DocumentBlock).

## §B. 두 provider 모두 거부 (Anthropic 레벨 게이팅, Bedrock-only 아님)

초기 가정 "`BEDROCK_UNSUPPORTED` 의 모든 항목은 Bedrock-only 제한"
이었으나, 실측해보니 여섯 표면은 **Anthropic API 자체에서 게이팅**.
CPaws 로 마이그레이션 한다고 풀리지 *않음*.

| 표면 | Bedrock | CPaws | 메모 |
|------|---------|-------|------|
| `computer_use_20250124` tool type | ⛔ 거부 | ⛔ 거부 | Anthropic 가 막음. 두 provider 모두 거부. |
| `tool_search_*` tool type | ⛔ 거부 | ⛔ 거부 | 별도 제품 채널 가능성. |
| `anthropic-beta: compaction-2025-09-17` | ⛔ 거부 | ⛔ 거부 (메시지 다름 — §D 참조) | beta flag 미릴리스. |
| Opus 4.7 의 Assistant prefill | ⛔ 거부 | ⛔ 거부 | Deprecation. Provider 무관. |
| Opus 4.7 의 sampling params (`temperature`, `top_p`, `top_k`) | ⛔ deprecated | ⛔ deprecated | Deprecation. Provider 무관. Opus 4.6 / Sonnet 4.6 은 양쪽 모두 legacy 수락. |
| Opus 4.7 의 `thinking.enabled_with_effort` | ⛔ 거부 | ⛔ 거부 | Opus 4.7 에서 글로벌하게 `adaptive` 로 마이그레이션. |

## §C. 행동 차이 (동일 표면, 다른 런타임 동작)

두 provider 모두 수락하지만 런타임 동작이 측정 가능하게 다른 표면.
가장 미묘한 발견 — 지속 관찰 필요.

### C.1 — 1시간 캐시: 쓰기는 성공, 즉시 읽기 실패 (CPaws)

Bedrock: `cache_control: {ttl: "1h"}` 첫 호출은 1h 캐시 생성, 두번째
호출이 캐시 적중 (`cache_read_input_tokens > 0`). `results/prompt_caching_verified.md`
§P-1 에서 검증.

**CPaws (2026-05-12, opus-4-7, ap-northeast-2)**: 첫 호출에서
`ephemeral_1h_input_tokens = 15025` 채워짐 ✅. 동일 prefix 의 두번째
호출은 `cache_read_input_tokens = 0` ❌ 이고
`ephemeral_5m_input_tokens = 8` 새로 씀. 1h 캐시 *쓰기* 는 *기록*되나
직후 후속 요청에서 *재현* 되지 않음.

가설 (미조사):
- CPaws 인프라의 캐시 propagation 지연.
- 1h 버킷이 5m 버킷과 다른 storage 계층에서 서빙.
- 리전 특이 (`ap-northeast-2` 에서만 검증).

테스트: `tests/caching/test_ttl_1h` — 현재 CPaws 에서 FAIL.

### C.2 — 짧은 응답 시 delta count 1 (CPaws)

Bedrock 의 스트리밍은 짧은 프롬프트 ("1, 2, 3, 4, 5 까지 응답") 에서도
다수의 `RawContentBlockDeltaEvent` 발생 — 보통 단어당 또는 몇 토큰당
1개. CPaws 는 동일 프롬프트에서 정확히 **1 개** 발생:
```
event_kinds: RawMessageStartEvent, RawContentBlockStartEvent,
             RawContentBlockDeltaEvent, RawMessageDeltaEvent,
             ParsedContentBlockStopEvent, ParsedMessageStopEvent,
             TextEvent
stop_reason: end_turn
preview: "1, 2, 3, 4, 5"
delta_count: 1
```

최종 텍스트 와 `stop_reason` 은 정상. *이벤트 청킹 입자도*만 다름.
인프라 차이 (CPaws 가 짧은 응답 버퍼링) 또는 SDK 버전 차이 가능성.
긴 응답으로 재검증 필요.

테스트: `tests/streaming/test_text_deltas` — `delta_count > 1` assert
하므로 CPaws 에서 FAIL.

## §D. 테스트 자체의 Bedrock 편향 (P4 후속)

두 테스트가 Bedrock 특정 에러 wording 에 묶여 있어 의미론적 contract 가
동일함에도 CPaws 에서 FAIL:

| 테스트 | 문제 | 수정 방향 |
|--------|------|-----------|
| `compaction_beta_header_rejected_on_bedrock` | `"invalid beta flag"` substring assert. CPaws 는 `"Unexpected value(s) compaction-2025-09-17 for the anthropic-beta header"` 거부. 둘 다 거부, wording 다름. | 두 패턴 OR matcher. |
| `async_client` | `AsyncAnthropicBedrock` 클래스 import → CPaws 에서도 `AWS_BEARER_TOKEN_BEDROCK` 요구. | Provider-aware: CPaws 에선 `AsyncAnthropic`. |

이는 contract 발견이 아니라 **테스트 suite 의 gap** — 두번째 provider
를 추가하면서 드러난.

## §E. CPaws 토큰 비용 관찰 (2026-05-12 실행)

`claude-opus-4-7` 전체 57개 테스트 스위트:

- 총 소요 시간: 187 초.
- API 호출: 61 회.
- Input 토큰: 284,650.
- Output 토큰: 2,479.
- Cache create (5m): 99,426.
- Cache create (1h): 27,041 (§C.1 에도 불구 작동).
- Cache read: 125,944.
- 청구 가능한 input 총합: 537,061 토큰.

1h 캐시 *쓰기* (27k) 는 성공하고 청구됨; §C.1 의 *재현 실패* 로
같은 run 의 후속 테스트가 캐시 적중 대신 재쓰기. 짧은 매트릭스는
영향 미미하지만 긴 세션에서 누적.

## §F. 이번 run 으로 suite 에 반영된 변경

- `tests/unsupported/test_server_tools.py` —
  `web_search`, `code_execution` 옆에 `web_fetch_20250910` 추가.
- `config.BEDROCK_UNSUPPORTED` — `server_tool_web_fetch` 추가.
- `config.BEDROCK_UNSUPPORTED` 주석 — `computer_use` 가 CPaws 에서도
  거부됨을 명시 (Anthropic 레벨 게이팅).

## §G. 후속 작업 (이번 baseline 범위 밖)

1. **Bedrock × CPaws 풀 매트릭스** — 두 provider × 3 모델 × 57 테스트.
   Cross-provider differences 섹션이 §A 항목들을 라벨 차이로 자동 노출.
2. **`web_fetch_20250910` 의 Bedrock baseline** — 현재 Bedrock baseline
   (2026-05-04) 은 `web_search` 와 `code_execution` 만 시험. 업데이트된
   `test_server_tools` 로 Bedrock 재실행해서 `web_fetch` 도 거부됨을
   확정.
3. **§C.1 캐시 1h read 심층 probe** — 1·2차 호출 사이 지연 변화,
   같은 리전 vs 교차 리전, `cache_read` 의 시간 추이 관찰.
4. **§D 테스트들의 provider-divergent contract 인코딩** —
   `test_sampling_deprecated` 패턴 (`info.contract = "rejected_on_X"
   vs "supported_on_Y"`) 적용.
5. **Files API 실측 확인** — 두 provider 모두 `client.files.*`
   `attribute_absent`. `anthropic` SDK 업그레이드 후 재시험.
