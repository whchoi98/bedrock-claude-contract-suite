# Testing Guidelines

## Test Structure

모든 `tests/<category>/test_*.py`는 다음을 노출해야 한다:

```python
NAME = "stable_short_id"           # --only-tests 필터에 사용
DESCRIPTION = "what is verified"   # matrix.md에 표시

def run(client, model) -> dict:
    return {
        "ok": bool,
        "info": {
            "contract": "...",     # _classify가 읽는 값
            ...
        },
        "error": str | None,
    }
```

## Harness Primitives (tests/_base.py)

반드시 import해서 사용. 재구현 금지:
- `Result` — 테스트 결과 dataclass
- `execute(name, description, fn)` — defensive runner (timing + error capture)
- `text_of(message)` — Messages API 응답에서 text block 연결
- `usage_breakdown(usage)` — cache_creation usage를 flat dict로 변환
- `is_unsupported_tool_rejection(message, tool_type)` — Bedrock 400 rejection 매칭

## Categories

| Directory | Scope |
|---|---|
| `messages/` | Messages API 기본: create, system, multi-turn, stop_sequences, metadata 등 |
| `streaming/` | SSE event schema, text/tool_use/thinking deltas |
| `tools/` | tool_choice, parallel, builtin tools, strict tool use |
| `thinking/` | adaptive, disabled, enabled-redirect, interleaved beta |
| `caching/` | 5m/1h cache, mixed buckets, multi-breakpoint |
| `context/` | 1M context beta header |
| `vision/` | base64 PNG, multi-image |
| `documents/` | PDF base64, PDF + citations |
| `citations/` | text document, search_result block |
| `token_counting/` | count_tokens rejection contract |
| `multilingual/` | Korean, Japanese |
| `client/` | AsyncAnthropicBedrock equivalence |
| `unsupported/` | Anthropic-direct-only endpoints |

## Cache Test Rules

1. 반드시 `secrets.token_hex(8)` salt를 cached prefix에 삽입
2. strict single-condition assertion 사용 (OR-fallback 금지)
3. `usage_breakdown()` 사용하여 cache_creation 필드 검증

## Running Tests

```bash
python3 run_all.py                          # 단일 모델
python3 run_all.py --all-models             # 3-모델 매트릭스
python3 run_all.py --only caching           # 카테고리 필터
python3 run_all.py --only-tests basic       # 개별 테스트
```

## New Test Checklist

1. `tests/<cat>/test_<name>.py` 생성 (NAME, DESCRIPTION, run 노출)
2. 모델별 동작 차이 → `info.contract` 값으로 분기 (별도 파일 금지)
3. 캐시 테스트 → cold-start salt 삽입 (ADR-001)
4. `tests._base` 헬퍼 재사용
5. `python3 run_all.py --only-tests <name>` 으로 smoke test
6. 새 카테고리 → 디렉토리에 CLAUDE.md 추가
