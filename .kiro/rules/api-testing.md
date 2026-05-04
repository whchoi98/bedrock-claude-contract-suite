# API Testing Rules

## Test vs Probe

| Situation | Location |
|---|---|
| 영구 contract 인코딩 | `tests/<cat>/test_*.py` |
| 여러 variant 탐색 | `scripts/probe_*.py` |
| 디버깅 세션용 유틸리티 | `scripts/<utility>.py` |
| 통계/반복 측정 | `results/*_probe.py` |

## Test Contract (필수)

```python
NAME = "stable_id"
DESCRIPTION = "short description"
def run(client, model) -> dict:
    return {"ok": bool, "info": {"contract": "...", ...}, "error": str | None}
```

## info.contract 값 규칙

- `"reject"` 포함 → ⛔ REJECTED
- `"deprecation_signals"` 키 → ⛔
- `config_rejected_on_bedrock=True` + `header_accepted=True` → 🟡 MIXED
- 그 외 → 🟢 SUPPORTED

## Probe Rules

- SDK 기반 프로브 → `make_client()` 사용
- 모델 리스트 → `config.ALL_MODELS` import (하드코딩 금지)
- 텍스트 추출 → `tests._base.text_of` 재사용
- 예외 처리 → 구체적 예외 (`except (httpx.HTTPError, ...)`)
- 출력 → `results/<probe_name>_probe.json`
- 독립 호출 → `concurrent.futures.ThreadPoolExecutor`로 병렬화
- 새 프로브 추가 시 → `scripts/CLAUDE.md`에 설명 추가

## Bedrock-Specific

- `extra_body` / `extra_headers` → SDK 스키마에 없는 새 모델 필드 전달용
- `anthropic_version: "bedrock-2023-05-31"` → Bedrock 필수 버전 헤더
- beta header → `config.py`의 `BETA_*` 상수 사용
- `BEDROCK_UNSUPPORTED` set → Anthropic-direct-only 기능 목록 (skip 대상)

## Findings Documentation

- 새 API contract 발견 → `results/docs_vs_reality.md`에 claim → evidence 행 추가
- 캐싱 관련 발견 → `results/prompt_caching_verified.md` 업데이트
- 인프라/엔드포인트 변경 → `docs/bedrock-api-endpoints-comparison.md` 업데이트
