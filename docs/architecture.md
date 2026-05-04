# Architecture

<p align="center">
  <a href="#한국어"><kbd>한국어</kbd></a>&nbsp;&nbsp;&nbsp;
  <a href="#english"><kbd>English</kbd></a>
</p>

---

# 한국어

## System Overview

`bedrock-claude-contract-suite`는 Amazon Bedrock 위에서 동작하는 Anthropic Claude 모델
(Opus 4.7 / Opus 4.6 / Sonnet 4.6)의 API contract를 자동으로 검증하는 Python
스위트입니다. 각 기능 surface(캐싱·도구·thinking·비전 등)를 카테고리별 테스트
파일로 인코딩해 🟢 supported / ⛔ rejected / 🟡 mixed / ❌ fail 4상태 매트릭스를
생성합니다. 검증 범위는 **`bedrock-runtime`의 InvokeModel API 경로**이고
`bedrock-mantle`은 의도적으로 scope 밖입니다.

## Components

### Configuration Layer
- **`config.py`** — `MODEL_ID`, `REGION`, `ALL_MODELS`, beta-header 상수.
  단일 모델 또는 매트릭스 모드의 진입점.
- **`client.py`** — `make_client()` 팩토리. `AWS_BEARER_TOKEN_BEDROCK`을
  읽어 `AnthropicBedrock` 인스턴스를 생성.

### Test Harness
- **`tests/_base.py`** — `Result` dataclass, `execute()` defensive runner,
  공유 헬퍼 (`text_of`, `usage_breakdown`,
  `is_unsupported_tool_rejection`).
- **`tests/<category>/test_*.py`** — 각 파일이 `NAME` / `DESCRIPTION` /
  `run(client, model)` contract를 노출. `run`은
  `{"ok": bool, "info": dict, "error": str|None}`을 반환.

### Runner & Reporter
- **`run_all.py`** — `tests/<cat>/test_*.py`를 자동 발견, 실행, 분류.
  `_classify` 함수가 `info.contract` 문자열을 4상태로 매핑.
  per-call 토큰 누적기 (`TokenAccumulator`)로 비용 추적.
- **`verify.sh`** — 인터랙티브 launcher. 비용 사전 안내 + 메뉴 기반 실행.

### Probes & Scripts
- **`scripts/intercept_proxy.py`** — Claude Code의 outbound HTTP를 가로채
  실제 outbound JSON 구조를 캡처 (cache_control / TTL / breakpoint 위치).
- **`scripts/probe_*.py`** — ad-hoc API contract 탐사 (structured outputs
  variants, token counting paths 등).
- **`results/variability_probe.py`**, **`stable_prefix_probe.py`** —
  cold-start salt 효과 입증용 통계 probe.

### Artifacts (Output)
- **`results/latest.{json,md}`** — 단일 모델 실행 결과.
- **`results/matrix.{json,md}`** — 3-모델 매트릭스 실행 결과.
- **`results/*_probe.json`** — raw probe 캡처.
- **`results/prompt_caching_verified.md`** — prompt caching contract 종합
  reference (TL;DR + claim → evidence 매핑).
- **`results/docs_vs_reality.md`** — Anthropic docs claims vs 실측 contract
  diff.
- **`logs/intercept.jsonl`** — intercept_proxy 캡처 로그.

### Documentation
- **`docs/bedrock-api-endpoints-comparison.md`** — Bedrock의 5가지 API 패턴
  (Responses / Chat Completions / Messages / Converse / InvokeModel)과 3개
  엔드포인트(bedrock / bedrock-runtime / bedrock-mantle) 종합 가이드.
- **`docs/decisions/`** — Architecture Decision Records.
- **`docs/runbooks/`** — 운영 절차서.

## Full Architecture Diagram

```
                                ┌─────────────────────────┐
                                │ Anthropic Build with    │
                                │ Claude documentation    │
                                └────────────┬────────────┘
                                             │ (claim source)
                                             ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                  bedrock-claude-contract-suite (this repo)                │
   │                                                                  │
   │   Configuration Layer                                            │
   │   ┌─────────────┐   ┌─────────────┐                              │
   │   │ config.py   │   │ client.py   │                              │
   │   └─────┬───────┘   └─────┬───────┘                              │
   │         │                 │                                      │
   │         ▼                 ▼                                      │
   │   Test Harness                                                   │
   │   ┌──────────────────────────────────────────────────┐           │
   │   │ tests/_base.py  (Result, execute, helpers)       │           │
   │   └────────┬─────────────────────────────────────────┘           │
   │            │ imports helpers                                     │
   │            ▼                                                     │
   │   ┌──────────────────────────────────────────────────┐           │
   │   │ tests/<category>/test_*.py × ~57 files           │           │
   │   │   NAME / DESCRIPTION / run(client, model)        │           │
   │   └────────┬─────────────────────────────────────────┘           │
   │            │ discovered + executed by                            │
   │            ▼                                                     │
   │   ┌──────────────────────────────────────────────────┐           │
   │   │ run_all.py — discover + execute + classify       │           │
   │   │   _classify() → 🟢/⛔/🟡/❌                       │           │
   │   │   TokenAccumulator → cost summary                │           │
   │   └────────┬───────────────────────┬─────────────────┘           │
   │            │                       │                             │
   │            ▼                       ▼                             │
   │   ┌─────────────────┐  ┌──────────────────────┐                  │
   │   │ results/        │  │ AnthropicBedrock SDK │ ────┐            │
   │   │  latest.{json}  │  │ (HTTP client)        │     │            │
   │   │  matrix.{json}  │  └──────────────────────┘     │            │
   │   └─────────────────┘                               │            │
   │                                                     │            │
   │   Probes / Scripts                                  │            │
   │   ┌──────────────────────────────────────────────┐  │            │
   │   │ scripts/probe_*.py, intercept_proxy.py       │ ─┤            │
   │   │ results/*_probe.py                           │  │            │
   │   └──────────────────────────────────────────────┘  │            │
   │                                                     │            │
   │   Findings (curated)                                │            │
   │   ┌──────────────────────────────────────────────┐  │            │
   │   │ results/prompt_caching_verified.md           │  │            │
   │   │ results/docs_vs_reality.md                   │  │            │
   │   └──────────────────────────────────────────────┘  │            │
   │                                                     │            │
   └─────────────────────────────────────────────────────┼────────────┘
                                                         │
                                                         ▼
                                ┌─────────────────────────────────────┐
                                │ Amazon Bedrock                      │
                                │  bedrock-runtime.{region}.aws.com   │
                                │   /model/{id}/invoke[-with-stream]  │
                                │  (bedrock-mantle: out of scope)     │
                                └─────────────────────────────────────┘
```

## Data Flow Summary

`config.py` → `client.py make_client()` → `run_all.py discover()` →
`tests/<cat>/test_*.py run()` → `AnthropicBedrock.messages.create()` →
`bedrock-runtime InvokeModel API` → response → `tests/_base.usage_breakdown()` →
`run_all.py _classify()` → `results/{latest,matrix}.{json,md}` +
`TokenAccumulator` summary

## Infrastructure

### Deployment Region

- `ap-northeast-2` (Seoul) — 단일 검증 리전. 다른 리전은 docs 비교 시
  필요 시 일회성 probe로 사용.

### External Dependencies

| Resource | Purpose |
|---|---|
| Amazon Bedrock InvokeModel API | 모든 contract 측정의 대상 |
| `AWS_BEARER_TOKEN_BEDROCK` (Bearer Token) | 인증 |
| `anthropic` Python SDK (`AnthropicBedrock`) | 클라이언트 |
| `httpx` | raw probe 호출 |
| `boto3` | 일부 probe의 SigV4 호출 |

### Generated Artifacts

- `results/latest.{json,md}` — 단일 실행 결과
- `results/matrix.{json,md}` — 3-모델 매트릭스
- `results/*_probe.json` — raw 캡처
- `logs/intercept.jsonl` — proxy 캡처

## Key Design Decisions

- **Cold-start salt 강제**: 캐시 테스트는 `secrets.token_hex(8)`을 prefix에
  주입해 매 실행마다 fresh write를 보장. Stable prefix는 이전 실행 상태를
  관찰하게 되어 false positive를 만든다.
  ([ADR-001](decisions/ADR-001-cold-start-salt-for-cache-tests.md) 참조)
- **`info.contract` 문자열 substring 분류**: enum 대신 자유 문자열에
  `"reject"` 부분 매칭. 모델별 contract 분기를 한 테스트로 표현 가능.
- **Mantle scope 제외**: `bedrock-mantle`은 별도 호스트 + 별도 모델 가용성을
  가지며 본 스위트의 범위를 벗어남. configuration 정보만 docs에 보존.
- **OR-fallback 어설션 금지**: `cold OR hot`처럼 약한 조건을 OR로 결합하면
  contract 변경이 silently 가려짐. strict single-condition 어설션 사용.

## Operations

운영 절차는 `docs/runbooks/`를 참조:

- 신규 모델 추가
- 매트릭스 baseline 갱신
- intercept proxy 운영
- token 비용 모니터링

---

# English

## System Overview

`bedrock-claude-contract-suite` is a Python suite that automatically verifies the
runtime API contract of Anthropic Claude models (Opus 4.7 / Opus 4.6 /
Sonnet 4.6) hosted on Amazon Bedrock. Each feature surface (caching,
tools, thinking, vision, etc.) is encoded as a categorized test file,
producing a four-state matrix of 🟢 supported / ⛔ rejected /
🟡 mixed / ❌ fail. The scope is **the InvokeModel API path on
`bedrock-runtime`**; `bedrock-mantle` is intentionally out of scope.

## Components

### Configuration Layer
- **`config.py`** — `MODEL_ID`, `REGION`, `ALL_MODELS`, beta-header
  constants. Single source of truth for what gets exercised.
- **`client.py`** — `make_client()` factory; reads
  `AWS_BEARER_TOKEN_BEDROCK` and constructs `AnthropicBedrock`.

### Test Harness
- **`tests/_base.py`** — `Result` dataclass, `execute()` defensive
  runner, shared helpers (`text_of`, `usage_breakdown`,
  `is_unsupported_tool_rejection`).
- **`tests/<category>/test_*.py`** — each exposes `NAME`,
  `DESCRIPTION`, and `run(client, model)` returning
  `{"ok": bool, "info": dict, "error": str|None}`.

### Runner & Reporter
- **`run_all.py`** — discovers `tests/<cat>/test_*.py`, executes them,
  classifies via `_classify` reading `info.contract`. Per-call token
  accumulator (`TokenAccumulator`) tracks cost.
- **`verify.sh`** — interactive launcher with cost notice + menu.

### Probes & Scripts
- **`scripts/intercept_proxy.py`** — captures Claude Code outbound HTTP
  to inspect cache_control / TTL / breakpoint shape.
- **`scripts/probe_*.py`** — ad-hoc API contract probes.
- **`results/variability_probe.py`**, **`stable_prefix_probe.py`** —
  statistical probes proving cold-start salt necessity.

### Artifacts (Output)
- **`results/latest.{json,md}`** — single-model run.
- **`results/matrix.{json,md}`** — 3-model matrix.
- **`results/*_probe.json`** — raw captures.
- **`results/prompt_caching_verified.md`** — caching contract reference
  (TL;DR + claim → evidence mapping).
- **`results/docs_vs_reality.md`** — docs vs measured contract diff.
- **`logs/intercept.jsonl`** — intercept_proxy capture log.

### Documentation
- **`docs/bedrock-api-endpoints-comparison.md`** — canonical guide to
  Bedrock's 5 API patterns and 3 endpoints.
- **`docs/decisions/`** — Architecture Decision Records.
- **`docs/runbooks/`** — operational runbooks.

## Full Architecture Diagram

(See the Korean section above — identical diagram.)

## Data Flow Summary

`config.py` → `client.make_client()` → `run_all.discover()` →
`tests/<cat>/test_*.py run()` → `AnthropicBedrock.messages.create()` →
`bedrock-runtime InvokeModel API` → response → `usage_breakdown()` →
`run_all._classify()` → `results/{latest,matrix}.{json,md}` +
`TokenAccumulator` summary.

## Infrastructure

### Deployment Region

- `ap-northeast-2` (Seoul) — single verification region. Other regions
  are used only for one-off probes when comparing to docs.

### External Dependencies

| Resource | Purpose |
|---|---|
| Amazon Bedrock InvokeModel API | Target of every contract measurement |
| `AWS_BEARER_TOKEN_BEDROCK` (Bearer Token) | Authentication |
| `anthropic` Python SDK (`AnthropicBedrock`) | Client |
| `httpx` | Raw probe calls |
| `boto3` | SigV4 calls in selected probes |

### Generated Artifacts

- `results/latest.{json,md}` — single run
- `results/matrix.{json,md}` — 3-model matrix
- `results/*_probe.json` — raw probe captures
- `logs/intercept.jsonl` — proxy capture

## Key Design Decisions

- **Cold-start salt enforcement**: every cache-related test injects
  `secrets.token_hex(8)` into the cached prefix to force fresh writes
  on every invocation. Stable prefixes observe pre-existing cache
  state, producing false positives.
- **Substring-based contract classification**: free strings in
  `info.contract` matched against `"reject"` substring. Allows a
  single test to express model-divergent contracts without an enum.
- **Mantle out of scope**: `bedrock-mantle` lives on a different host
  with different model gating; documenting it here would conflate
  measurement scope. Configuration is kept in `docs_vs_reality.md`
  for users who need it.
- **No OR-fallback assertions**: weak OR-combined conditions hide
  contract drift silently. Use strict single-condition assertions.

## Operations

See `docs/runbooks/` for:
- adding a new model
- refreshing matrix baseline
- intercept proxy operation
- token cost monitoring
