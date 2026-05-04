# Architecture Reference

> 전체 아키텍처 다이어그램과 상세 설명은 `docs/architecture.md` 참조.

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│              bedrock-claude-contract-suite               │
│                                                         │
│  config.py ──→ client.py ──→ AnthropicBedrock           │
│      │                           │                      │
│      ▼                           ▼                      │
│  run_all.py ──→ tests/<cat>/test_*.py                   │
│      │              │                                   │
│      │              ▼                                   │
│      │         tests/_base.py (Result, execute, ...)    │
│      │                                                  │
│      ▼                                                  │
│  results/matrix.{json,md}                               │
│  results/latest.{json,md}                               │
└─────────────────────────────────────────────────────────┘
         │
         ▼
  Amazon Bedrock (bedrock-runtime InvokeModel API)
```

## Data Flow

1. `config.py` → 모델 ID, 리전, beta-header 상수 제공
2. `client.py:make_client()` → `AnthropicBedrock` 인스턴스 생성
3. `run_all.py` → `tests/` 하위 모듈 자동 발견 → `execute()` 로 실행
4. 각 테스트 → `run(client, model)` 호출 → `{"ok", "info", "error"}` 반환
5. `_classify()` → `info.contract` 기반 4상태 분류 (🟢/⛔/🟡/❌)
6. `TokenAccumulator` → per-call 토큰 사용량 누적
7. 결과 → `results/` 디렉토리에 JSON + Markdown 출력

## Key Design Decisions

- **ADR-001**: 캐시 테스트의 cold-start salt — `secrets.token_hex(8)` 필수
- **ADR-002**: 런타임 secret scanning — dual-channel (PreToolUse + git staged)
- 전체 ADR 목록: `docs/decisions/`

## Endpoint Scope

- **In scope**: `bedrock-runtime.{region}.amazonaws.com` (InvokeModel API)
- **Out of scope**: `bedrock-mantle.{region}.api.aws` (Anthropic-shape endpoint)
- 엔드포인트 비교: `docs/bedrock-api-endpoints-comparison.md`
