# Project Context & Conventions

## Architecture

- `config.py` — 모델 ID, 리전, beta-header 상수의 단일 진실 소스
- `client.py` — `make_client()` 팩토리 (`AWS_BEARER_TOKEN_BEDROCK` 읽기)
- `run_all.py` — `tests/<cat>/test_*.py` 자동 발견 → 실행 → `_classify` 분류 → 토큰 추적
- `tests/_base.py` — 공유 harness: `Result`, `execute()`, `text_of()`, `usage_breakdown()`, `is_unsupported_tool_rejection()`

## Contract Classification

`run_all.py:_classify`가 `info.contract` 문자열을 4상태로 매핑:
- `"reject"` 포함 → ⛔ REJECTED
- `"deprecation_signals"` 키 존재 → ⛔
- `config_rejected_on_bedrock=True` AND `header_accepted=True` → 🟡 MIXED
- 그 외 → 🟢 SUPPORTED

## Conventions

1. **Test contract**: 모든 `tests/<cat>/test_*.py`는 반드시 `NAME: str`, `DESCRIPTION: str`, `run(client, model) -> {"ok": bool, "info": dict, "error": str|None}` 노출
2. **Cold-start salt**: 캐시 테스트는 반드시 `secrets.token_hex(8)`을 cached prefix에 삽입. 안정 prefix는 실행 간 상태를 공유해 false positive 유발
3. **Strict assertions**: `fresh_path or hot_path` 같은 OR-fallback 금지. 관찰하려는 특정 신호를 pin할 것 (`create_1h > 0` 등)
4. **Model-divergent contracts**: 모델별 동작 차이는 같은 테스트 내에서 `info.contract` 값으로 인코딩. 별도 파일 분리 금지. 패턴: `tests/messages/test_sampling_deprecated.py`
5. **Endpoint scope**: `bedrock-runtime` Invoke API만 대상. `bedrock-mantle`은 scope 밖
6. **Import rules**: `text_of`, `usage_breakdown`, `is_unsupported_tool_rejection`는 `tests._base`에서 import. 재구현 금지. `MODEL_ID`, `REGION`, `ALL_MODELS`는 `config`에서 import

## Auto-Sync Rules

코드 변경 시 자동 동기화:
- `tests/` 하위 새 디렉토리 → 해당 디렉토리에 CLAUDE.md 생성
- 새 테스트 파일 → NAME/DESCRIPTION/run() contract 준수
- 새 공유 헬퍼 → `tests/_base.py`에 추가 (파일별 중복 금지)
- 캐시 관련 테스트 → cold-start salt 필수
- 새 환경변수 → `verify.sh` 토큰 안내 및 `.env.example` 업데이트
- 새 API contract 발견 → `results/docs_vs_reality.md` 행 추가
- ADR 번호 → `docs/decisions/ADR-*.md` 최고 번호 + 1

## Environment

- `AWS_BEARER_TOKEN_BEDROCK` (필수) — Bedrock API Key
- `AWS_REGION` (선택, 기본 `ap-northeast-2`)
- `BEDROCK_MODEL_ID` (선택, 기본 `global.anthropic.claude-opus-4-7`)
