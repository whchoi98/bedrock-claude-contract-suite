# Code Style Rules

## Formatting

- indent: 4 spaces (Python, shell), 2 spaces (md, yml, json)
- UTF-8, LF line endings, trailing whitespace 제거, 파일 끝 newline
- `.editorconfig` 참조

## Python

- Python 3.9+ 호환 (f-string OK, `match` 문 사용 금지)
- `from __future__ import annotations` 사용 (type hint forward ref)
- 타입 힌트: `dict[str, Any]`, `str | None` (3.9 호환 시 `from __future__` 필수)

## Import Rules

- `text_of`, `usage_breakdown`, `is_unsupported_tool_rejection` → `tests._base`에서 import
- `MODEL_ID`, `REGION`, `ALL_MODELS` → `config`에서 import
- `make_client()` → `client`에서 import
- 위 항목을 재선언하거나 재구현하지 않을 것

## Exception Handling

- `except Exception` 대신 구체적 예외 사용 (`except (httpx.HTTPError, ...)`)
- `tests/_base.py:execute()`는 예외적으로 `except Exception` 허용 (defensive runner)

## Naming

- 테스트 파일: `tests/<category>/test_<snake_case>.py`
- NAME 상수: stable short identifier (변경 시 matrix 호환성 깨짐)
- 프로브 파일: `scripts/probe_<name>.py`
- 프로브 출력: `results/<name>_probe.json`

## Comments

- 서술적/변경이력 코멘트 금지 ("previous version", "now corrected" 등)
- hot-path 문자열은 모듈 레벨 상수로 추출
