# Onboarding Guide

## Prerequisites

- Python 3.9+
- `anthropic`, `httpx`, `boto3` 패키지
- Amazon Bedrock 계정 (ap-northeast-2 리전, Claude Opus/Sonnet 모델 접근 권한)
- Bedrock API Key (`AWS_BEARER_TOKEN_BEDROCK`)

## Setup

```bash
pip install anthropic httpx boto3
cp .env.example .env
# .env에 AWS_BEARER_TOKEN_BEDROCK 설정
source .env
python3 run_all.py --only-tests basic   # smoke test (~$0.05)
```

## Full Matrix Run

3-모델 매트릭스 실행 비용: 약 **$5 USD** (3 models × ~57 tests × ~176 API calls).

```bash
./verify.sh          # 인터랙티브 (비용 안내 포함)
python3 run_all.py --all-models   # 직접 실행
```

결과: `results/latest.{json,md}` (단일 모델), `results/matrix.{json,md}` (매트릭스)

## Contributing a New Test

1. `tests/<cat>/test_<name>.py` 생성
2. `NAME`, `DESCRIPTION`, `run(client, model)` 노출
3. 캐시 테스트 → `secrets.token_hex(8)` salt 삽입
4. `tests._base` 헬퍼 재사용 (재구현 금지)
5. `python3 run_all.py --only-tests <name>` smoke test
6. 새 카테고리 → 디렉토리에 CLAUDE.md 추가

## Essential Reading

| Document | Purpose |
|---|---|
| `CLAUDE.md` (root) | 컨벤션, 커맨드, sync rules |
| `results/prompt_caching_verified.md` | 캐싱 contract 종합 reference |
| `results/docs_vs_reality.md` | Anthropic docs vs 실측 contract diff |
| `docs/bedrock-api-endpoints-comparison.md` | Bedrock 엔드포인트 가이드 |
| `docs/decisions/ADR-001-*` | cold-start salt 근거 |

## Common Pitfalls

- 캐시 테스트에 salt 없음 → 실행 간 variance (ADR-001)
- OR-fallback assertion → contract drift 은폐
- 모델 리스트/리전 하드코딩 → `config.ALL_MODELS`, `config.REGION` import
- `response_format` 사용 → Anthropic은 `output_config.format` (OpenAI 네이밍 아님)
