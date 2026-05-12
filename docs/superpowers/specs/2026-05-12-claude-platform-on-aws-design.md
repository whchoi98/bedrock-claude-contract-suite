# Claude Platform on AWS — Provider 통합 디자인

- **Date**: 2026-05-12
- **Status**: Approved (design phase)
- **Author**: WooHyung Choi
- **Related**: `CLAUDE.md` (root), `docs/architecture.md`,
  `docs/bedrock-api-endpoints-comparison.md`

## Context

`bedrock-claude-contract-suite` 는 현재 Amazon Bedrock Invoke API
(`bedrock-runtime.{region}.amazonaws.com`) 의 Anthropic Claude 호스팅 contract만
검증한다. 2026년 GA 된 **Claude Platform on AWS** (`aws-external-anthropic.{region}.api.aws`)
는 동일한 모델을 AWS Marketplace 청구 + IAM/API key 인증으로 호스팅하지만,
**Anthropic 직접 API 와 동일한 릴리스 일정과 기능 contract** 를 가진다고
명시돼있다 (출처: <https://code.claude.com/docs/ko/claude-platform-on-aws>).

본 디자인은 이 두번째 표면을 verification suite 에 추가해서

1. Bedrock 에서 거부되는 기능이 CPaws 에서 정말 작동하는지를 **데이터로** 검증하고,
2. 두 표면을 한 매트릭스에서 비교 가능한 산출물을 만드는 것을 목표로 한다.

## Goals

- 동일한 57개 contract 테스트를 **Bedrock × CPaws × 3 모델 = 6 run** 으로 실행.
- `results/matrix.{json,md}` 가 두 provider 의 결과를 자연스럽게 비교할 수 있는 구조로 출력.
- "Bedrock 에서 막힘 / CPaws 에서 통과" 인 기능을 자동 추출하는 cross-provider diff 섹션.
- 기존 단일-provider 호출(`python3 run_all.py [...]`) 은 동작 변화 없음 (backward compatible CLI).

## Non-goals

- **테스트 본문 수정 금지**. `tests/<cat>/test_*.py` 는 한 줄도 바꾸지 않는다.
  `unsupported/` 테스트가 CPaws 에서 ❌로 떨어지는 결과 자체를 데이터로 본다.
- **Mantle 지원 추가 없음**. `feedback_mantle_opt_in` 메모리의 분류 유지.
- **SigV4 인증 경로 미지원**. Workspace API key 단일.
- **Anthropic 직접 API endpoint(`api.anthropic.com`) 추가 없음**. 본 작업은 AWS 위의 두 표면만.
- **Provider-divergent contract 인코딩 (sampling_deprecated 패턴을 unsupported/ 로 확장) 없음**. Follow-up 작업.

## §1. Architecture

### 1.1 Provider 추상화 모듈

```
providers/
  __init__.py     # make_client(provider, alias), resolve_model(provider, alias)
  bedrock.py      # AnthropicBedrock + AWS_BEARER_TOKEN_BEDROCK
  cpaws.py        # Anthropic + base_url + x-api-key + workspace 헤더
client.py         # 얇은 wrapper — 기존 `from client import make_client` 후방호환
                  # → providers.make_client("bedrock", default alias) 위임
```

### 1.2 CPaws 클라이언트 구성 (Workspace API key 인증)

```python
# providers/cpaws.py
import os, sys
from anthropic import Anthropic

def make_client(region: str) -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    if not api_key:
        print("ERROR: ANTHROPIC_AWS_API_KEY not set.", file=sys.stderr)
        sys.exit(2)
    if not workspace_id:
        print("ERROR: ANTHROPIC_AWS_WORKSPACE_ID not set.", file=sys.stderr)
        sys.exit(2)
    return Anthropic(
        base_url=f"https://aws-external-anthropic.{region}.api.aws",
        api_key=api_key,
        default_headers={"anthropic-workspace-id": workspace_id},
    )
```

### 1.3 Config 변경

```python
# config.py
PROVIDERS = ("bedrock", "cpaws")
DEFAULT_PROVIDER = "bedrock"

MODEL_ALIASES = {
    "opus-4-7":   {"bedrock": "global.anthropic.claude-opus-4-7",
                   "cpaws":   "claude-opus-4-7"},
    "opus-4-6":   {"bedrock": "global.anthropic.claude-opus-4-6-v1",
                   "cpaws":   "claude-opus-4-6"},
    "sonnet-4-6": {"bedrock": "global.anthropic.claude-sonnet-4-6",
                   "cpaws":   "claude-sonnet-4-6"},
}

ALL_MODELS = list(MODEL_ALIASES.keys())   # alias 리스트로 변경
```

- 기존 `ALL_MODELS` 가 Bedrock 모델 ID 리스트였던 것을 **alias 리스트**로 바꾼다.
- Bedrock-only 호출 경로는 alias → bedrock model id 해석으로 그대로 작동.

### 1.4 Auth (Workspace API key 단일)

```bash
# .env additions
ANTHROPIC_AWS_API_KEY=sk-ant-xxxxx           # CPaws workspace API key
ANTHROPIC_AWS_WORKSPACE_ID=wrkspc_01ABCDEFGHIJ
CPAWS_REGION=us-east-1                       # 선택 — 없으면 AWS_REGION 폴백
```

- Bedrock 의 `AWS_BEARER_TOKEN_BEDROCK` 은 그대로 유지.
- 두 변수 모두 `verify.sh` 시작 시 검증 (해당 provider 가 활성일 때만).

## §2. Runner · Matrix · Output

### 2.1 CLI 변경 (`run_all.py`)

신규 플래그 `--providers <p1> <p2> ...`. 기본값 `("bedrock",)` 로 후방호환.

```bash
# 기존 동작 — 변화 없음
python3 run_all.py
python3 run_all.py --all-models
python3 run_all.py --only caching

# 신규
python3 run_all.py --providers cpaws --all-models
python3 run_all.py --providers bedrock cpaws --all-models     # 풀 매트릭스 (6 runs)
python3 run_all.py --providers bedrock cpaws --only-tests cache_ttl_1h
```

### 2.2 매트릭스 구조 — 2D nested

```python
# 신규
matrix: dict[str, dict[str, payload]]   # {provider: {alias: payload}}
```

```json
{
  "bedrock": {
    "opus-4-7":   { ... payload ... },
    "opus-4-6":   { ... payload ... },
    "sonnet-4-6": { ... payload ... }
  },
  "cpaws": {
    "opus-4-7":   { ... payload ... },
    "opus-4-6":   { ... payload ... },
    "sonnet-4-6": { ... payload ... }
  }
}
```

**Breaking change**: 기존 `matrix.json` 은 `dict[model_id, payload]` 의 1D 구조였다.
본 프로젝트의 외부 consumer 가 없고 매트릭스 스냅샷이 사람-읽는 산출물이므로
마이그레이션 코드 없이 V2 로 전환한다. 과거 `matrix-2026-05-04.json` 같은 파일은
**그 자리에 보존** (히스토리는 디스크에 살아있음).

### 2.3 Markdown 렌더링 (`results/matrix.md`)

4섹션 구조:

1. **Per-provider × per-model totals** — provider, model alias, 🟢/⛔/🟡/❌/Total 의 단일 비교표.
2. **Test × Model matrix per provider** — provider 별 sub-섹션, 그 안은 기존 카테고리별 테이블 (열=모델 alias, 행=테스트).
3. **Cross-provider differences** *(이 디자인의 킬러 섹션)* — 같은 (test, alias) 쌍에서 두 provider 가 다르게 분류된 경우만 표시.
   ```
   | Test | Model | bedrock | cpaws |
   | computer_use_tool_rejected | opus-4-7 | ⛔ | ❌ |
   ```
4. **Inter-model differences** — 기존 섹션 유지, provider 별 sub-그루핑.

### 2.4 단일-모델 (`latest.{json,md}`)

```bash
python3 run_all.py                       # latest.json — provider 필드 "bedrock"
python3 run_all.py --providers cpaws     # latest.json — provider 필드 "cpaws"
```

`latest.json` payload 최상위에 `"provider": "<name>"` 필드 신설. 후방호환:
필드 없으면 `"bedrock"` 으로 간주.

### 2.5 토큰 트래킹

```
-- per-model tokens: bedrock / opus-4-7 --
== provider-wide tokens: bedrock ==
== provider-wide tokens: cpaws ==
== matrix-wide tokens (all providers) ==
```

- provider 별 합산을 별도 섹션으로 출력 → Bedrock 청구서 vs Marketplace 청구서 비교에 직접 도움.

## §3. Risks · Phases · Open questions

### 3.1 Risks

| # | 위험 | 영향 | 완화 |
|---|---|---|---|
| 1 | **CPaws 리전 가용성**: 프로젝트 기본 `ap-northeast-2` 에 워크스페이스가 없을 가능성. | 모든 호출 4xx. | `CPAWS_REGION` 환경변수 도입. smoke run 으로 사전 확인. |
| 2 | **모델 ID 매핑 오류**: `opus-4-6-v1` ↔ `claude-opus-4-6` 매핑이 추측. | alias 1행이 전부 ❌. | P1 종료 후 smoke run `--only-tests messages_create` 로 alias 검증. |
| 3 | **`is_unsupported_tool_rejection` 의 Bedrock 편향**: 거부 메시지 패턴이 Bedrock 특정 문구에 묶임. | unsupported/ 의 일부 결과가 부정확. | P4 에서 실측 메시지 추가. 헬퍼 변경은 **테스트 본문이 아니라 `_base.py`** 라 §1 "테스트 코드 0 변경" 원칙과 별개로 허용. |
| 4 | **양쪽 청구**: 풀 매트릭스 1회 = Bedrock + Marketplace 두 청구. | 운영 비용 약 2배. | `verify.sh` 비용 경고에 명시. 기본 호출은 `--providers bedrock` 단일 유지. |
| 5 | **Type hint 충돌**: 테스트가 `AnthropicBedrock` 으로 typed 됐을 경우. | 정적 분석 경고 (런타임은 정상). | 영향 받는 곳만 `anthropic.AnthropicBedrock \| anthropic.Anthropic` union 또는 `Any`. |

### 3.2 Phased delivery

| Phase | 범위 | 검증 기준 |
|---|---|---|
| **P1 — Provider 코드** | `providers/`, `client.py` wrapper, `config.MODEL_ALIASES`, `run_all.py --providers`. **테스트 코드 0건 수정.** | `python3 run_all.py --providers cpaws --only-tests messages_create` smoke 통과. |
| **P2 — 매트릭스 렌더링** | 2D nested matrix.json + 4섹션 markdown (per-provider totals, per-provider matrices, cross-provider diff, inter-model diff). | 양쪽 provider 풀 매트릭스 1회 실행. `results/matrix.{json,md}` 시각 검수. |
| **P3 — 운영 산출물** | `.env.example`, `verify.sh` 비용 경고, `docs/architecture.md`, `tests/CLAUDE.md` endpoint scope, CHANGELOG, root `CLAUDE.md`. | 문서 정합성 점검 (sync-docs skill). |
| **P4 — 실측 보완 (선택)** | `is_unsupported_tool_rejection` 패턴 보완, `results/cpaws_findings.md` baseline. | 첫 매트릭스 실측 데이터 기반. |

P1, P2 는 함께 머지될 때 사용자 입장에서 의미가 있다 (P1 단독으로는 매트릭스 형식이 전환 안 됨). P3 는 독립.

### 3.3 Open questions (실행 전 확인)

1. CPaws 워크스페이스가 이미 프로비저닝됐는가?
2. 워크스페이스 리전은? (`us-east-1`, `us-west-2`, `ap-northeast-2` 중)
3. 워크스페이스에 3개 모델 (opus-4-7, opus-4-6, sonnet-4-6) 전부 활성화돼있나?
4. P4 의 `is_unsupported_tool_rejection` 확장이 발생할 때, `tests/_base.py` 변경을 §1 "테스트 코드 0 변경" 원칙의 예외로 명시적으로 허용하는가? (디자인은 헬퍼는 테스트 본문이 아니라는 입장)

## 4. Verification strategy

각 Phase 종료 시 다음 명령으로 검증:

```bash
# P1 — provider 모듈 단독 import 가능, smoke 호출 통과
python3 -c "from providers import make_client; c = make_client('cpaws', 'opus-4-7')"
python3 run_all.py --providers cpaws --only-tests messages_create

# P2 — 풀 매트릭스 1회, 4섹션 구조 확인
python3 run_all.py --providers bedrock cpaws --all-models
test -f results/matrix.json && test -f results/matrix.md

# P3 — 문서 동기화 점검
grep -l "AWS_BEARER_TOKEN_BEDROCK" .env.example verify.sh   # 양쪽에 ANTHROPIC_AWS_* 도 있어야 함
grep -l "providers" docs/architecture.md
```

## 5. References

- Claude Platform on AWS 문서: <https://code.claude.com/docs/ko/claude-platform-on-aws>
- Anthropic 모델 목록: <https://platform.claude.com/docs/en/about-claude/models/overview>
- 본 프로젝트 메모리:
  - `feedback_mantle_opt_in` — Mantle 의 분류와 본 작업의 경계
  - `project_mantle_endpoint_host` — Mantle 호스트와 CPaws 호스트의 차이
  - `feedback_data_point_principle` — `unsupported/` 결과를 데이터로 보는 근거
- 관련 ADR: `docs/decisions/` (필요 시 본 작업 결과로 ADR-NNN 추가)
