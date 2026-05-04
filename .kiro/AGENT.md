# bedrock-claude-contract-suite

Amazon Bedrock의 Anthropic Claude API runtime contract를 자동 검증하는 Python 스위트.
각 기능 surface(caching, tools, thinking, vision 등)를 카테고리별 테스트로 인코딩해
🟢 supported / ⛔ rejected / 🟡 mixed / ❌ fail 매트릭스를 생성한다.

## Quick Reference

- **Language**: Python 3.9+ (no build system, plain modules)
- **SDK**: `anthropic` (`AnthropicBedrock` client)
- **Auth**: `AWS_BEARER_TOKEN_BEDROCK` (Bearer token)
- **Region**: `ap-northeast-2` (default, configurable via `AWS_REGION`)
- **Entry points**: `run_all.py`, `verify.sh`

## Key Commands

```bash
python3 run_all.py                          # single-model run
python3 run_all.py --all-models             # 3-model matrix
python3 run_all.py --only caching tools     # category filter
python3 run_all.py --only-tests cache_ttl_1h # test filter
./verify.sh                                 # interactive launcher
```

## Project Layout

| Path | Role |
|---|---|
| `config.py` | MODEL_ID, REGION, ALL_MODELS, beta-header constants |
| `client.py` | `make_client()` factory |
| `run_all.py` | test discovery, execution, classification, token tracking |
| `tests/_base.py` | `Result`, `execute()`, `text_of()`, `usage_breakdown()`, `is_unsupported_tool_rejection()` |
| `tests/<category>/test_*.py` | individual contract tests |
| `scripts/` | one-off probes and intercept proxy |
| `results/` | matrix output + verified findings |
| `docs/` | architecture, ADRs, runbooks |
| `fixtures/` | binary test inputs (PNG, PDF) |

## Steering & Rules

Kiro는 `.kiro/steering/**/*.md`를 자동 로드한다.
프로젝트 컨벤션, 테스트 규칙, 보안 정책은 steering 디렉토리를 참조할 것.
