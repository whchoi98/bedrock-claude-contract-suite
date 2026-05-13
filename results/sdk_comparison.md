# `Anthropic` vs `AnthropicAWS` SDK — 비교 (Python `anthropic` 0.96.0 기준)

> 이 프로젝트가 Claude Platform on AWS 를 호출할 때 두 가지 경로 — 표준
> `Anthropic` 클래스에 `base_url` 을 직접 주입하는 *workaround* 와, 공식
> `AnthropicAWS` 클래스 — 사이의 실측 차이 분석. 2026-05-13 기준,
> AnthropicAWS 는 **beta** 상태.
>
> 본 프로젝트의 `providers/cpaws.py` 는 본 비교 후 AnthropicAWS 로 전환됨.

## TL;DR

| 결정 측면 | `Anthropic` + base_url override | `AnthropicAWS` |
|---|---|---|
| 패키지 | `anthropic` (표준) | `anthropic[aws]` (extras, 단 같은 wheel 에 포함) |
| 상태 | GA, 1.x 안정 | **Beta** |
| 클래스 위치 | `anthropic.Anthropic` | `anthropic.lib.aws._client.AnthropicAWS` |
| 클래스 관계 | base | **AnthropicAWS ⊂ Anthropic** (subclass) |
| 환경변수 자동 인식 | ❌ (caller가 다 읽어야) | ✅ `ANTHROPIC_AWS_API_KEY`, `ANTHROPIC_AWS_WORKSPACE_ID`, `AWS_REGION`, `AWS_DEFAULT_REGION` |
| `base_url` 자동 구성 | ❌ (caller가 만들어야) | ✅ `aws-external-anthropic.{region}.api.aws` 자동 |
| `anthropic-workspace-id` 헤더 | 수동 (`default_headers`) | 자동 (`default_headers` property override) |
| SigV4 인증 | ❌ 미지원 (x-api-key 만) | ✅ `_prepare_request` 에서 자동 서명 |
| `skip_auth` 모드 | N/A | ✅ 게이트웨이 위임 시나리오용 |
| `inference_geo` 등 CPaws 특이 파라미터 | 작동은 함 (Messages API 에 그대로 전달) | 첫급 지원 |
| Async 클래스 | `AsyncAnthropic` | `AsyncAnthropicAWS` |
| Bedrock과 한 코드에서 공존 | 쉬움 (둘 다 generic) | 보통 (mypy 가 union 필요) |
| 본 프로젝트 영향 | `providers/cpaws.py` workaround | 전환 완료 (2026-05-13) |

## §A. 클래스 계층

```
SyncAPIClient
  └─ Anthropic
        └─ AnthropicAWS   (← AWS-특이 동작만 override)
```

`AnthropicAWS` 가 **`Anthropic` 의 subclass**. 즉 일단 생성되면 `.messages.create(...)`,
`.beta.*`, `.models.list()` 등 메소드는 100% 동일. 차이는 *생성과 요청 직전 처리* 에만 있음.

```python
import inspect
from anthropic import Anthropic, AnthropicAWS

[c.__name__ for c in AnthropicAWS.__mro__]
# ['AnthropicAWS', 'Anthropic', 'SyncAPIClient', 'BaseClient', 'Generic', 'object']

# 인스턴스 메소드는 동일
set(dir(Anthropic)) - set(dir(AnthropicAWS))  # 차집합 0
```

## §B. 생성자 signature 차이

### `Anthropic.__init__`
```python
def __init__(
    self,
    *,
    api_key: str | None = None,
    auth_token: str | None = None,
    base_url: str | httpx.URL | None = None,
    timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
    max_retries: int = 2,
    default_headers: Mapping[str, str] | None = None,
    default_query: Mapping[str, object] | None = None,
    http_client: httpx.Client | None = None,
    _strict_response_validation: bool = False,
) -> None: ...
```

### `AnthropicAWS.__init__` — 추가 파라미터들
```python
def __init__(
    self,
    *,
    api_key: str | None = None,
    aws_access_key: str | None = None,           # 추가
    aws_secret_key: str | None = None,           # 추가
    aws_region: str | None = None,               # 추가
    aws_profile: str | None = None,              # 추가
    aws_session_token: str | None = None,        # 추가
    workspace_id: str | None = None,             # 추가
    skip_auth: bool = False,                     # 추가
    base_url: str | httpx.URL | None = None,     # 동일 (자동 derive 됨)
    timeout: ...,                                 # 동일
    max_retries: int = 2,
    default_headers: ...,
    default_query: ...,
    http_client: ...,
    _strict_response_validation: bool = False,
    auth_token: str | None = None,               # 호환용
) -> None: ...
```

→ **7개 신규 파라미터**. 모두 *AWS 인증/리소스* 관련.

## §C. 생성자 내부 동작 (`AnthropicAWS.__init__`)

```python
def __init__(self, *, api_key=None, aws_*, workspace_id=None, skip_auth=False, ...):
    validate_credentials(aws_access_key=..., aws_secret_key=...)

    self._use_sigv4 = resolve_auth_mode(
        api_key=api_key, aws_access_key=..., aws_secret_key=..., aws_profile=...
    )
    resolved_api_key = resolve_api_key(api_key=api_key, use_sigv4=self._use_sigv4)
    resolved_region  = resolve_region(aws_region)
    self.workspace_id = resolve_workspace_id(workspace_id)   # 누락 시 AnthropicError
    base_url = resolve_base_url(base_url, region=resolved_region)

    super().__init__(
        api_key=resolved_api_key,
        auth_token=auth_token,
        base_url=base_url,
        ...
    )
```

### `resolve_*` helper 들의 동작

| Helper | 입력 우선순위 |
|---|---|
| `resolve_auth_mode` | 명시 `api_key` → `aws_access_key`+`aws_secret_key` → `aws_profile` → 환경 `ANTHROPIC_AWS_API_KEY` → 기본 AWS 자격증명 체인 (SigV4 결정) |
| `resolve_api_key` | 명시 `api_key` → 환경 `ANTHROPIC_AWS_API_KEY` (단 SigV4 모드 시 None) |
| `resolve_region` | 명시 `aws_region` → `AWS_REGION` → `AWS_DEFAULT_REGION` |
| `resolve_workspace_id` | 명시 `workspace_id` → `ANTHROPIC_AWS_WORKSPACE_ID` |
| `resolve_base_url` | 명시 `base_url` → `https://aws-external-anthropic.{region}.api.aws` |

→ **환경변수 fallback 이 SDK 내부에 캡슐화됨**. 사용자는 둘 중 하나만 (명시 인자 또는 env) 제공하면 됨.

## §D. SigV4 인증 — 차별점

`Anthropic` 은 SigV4 를 모름 (당연 — AWS 무관 클래스). `AnthropicAWS` 는
`_prepare_request` 메소드를 **override** 해서 SigV4 서명 주입:

```python
@override
def _prepare_request(self, request: httpx.Request) -> None:
    if not self._use_sigv4:
        return                                      # API key 모드는 skip

    from ._auth import get_auth_headers

    data = request.read().decode()
    headers = get_auth_headers(
        method=request.method,
        url=str(request.url),
        headers=request.headers,
        aws_access_key=self.aws_access_key,
        aws_secret_key=self.aws_secret_key,
        aws_session_token=self.aws_session_token,
        region=self.aws_region,
        profile=self.aws_profile,
        data=data,
        service_name="aws-external-anthropic",      # ★ 중요: 서명 service name
    )
    request.headers.update(headers)
```

→ SigV4 service name 이 `aws-external-anthropic` 으로 고정. 매 요청마다
자동으로 `Authorization: AWS4-HMAC-SHA256 ...` 헤더가 들어감.

**`Anthropic` 으로 SigV4 를 *수동* 구현하려면**: `httpx.Client` 의
event_hooks 에 서명 함수를 끼우거나 `httpx.Auth` 를 구현해서 주입.
공식 example 없음 → 별도 라이브러리 (boto3 의 SigV4Auth 등) 필요.
즉 generic 경로로 SigV4 가능하지만 *상당한 보일러플레이트*.

## §E. `anthropic-workspace-id` 헤더 자동 주입

`Anthropic` 의 `default_headers` property 는 platform headers (User-Agent 등) 만 반환.
`AnthropicAWS` 가 이를 override 해서 workspace ID 추가:

```python
@property
@override
def default_headers(self) -> dict[str, str | Omit]:
    headers = {**super().default_headers}
    if self.workspace_id is not None:
        headers["anthropic-workspace-id"] = self.workspace_id
    return headers
```

→ 사용자가 `default_headers={"anthropic-workspace-id": ...}` 를 *수동* 으로
넘기지 않아도 자동 적용. workspace 가 누락된 채 호출하면 SDK 가 *생성 시점에*
`AnthropicError("No workspace ID found...")` 발생.

## §F. `skip_auth` 모드 — 게이트웨이 위임 시나리오

`AnthropicAWS(skip_auth=True)` 로 생성하면:
- SigV4 서명 *생략*
- API key 해소도 *생략*
- 단 `base_url` 과 `workspace_id` 는 여전히 검증

용도: 사내 프록시/LLM 게이트웨이가 *그 너머에서* SigV4 서명을 추가하는 경우.
요청을 unsigned 로 게이트웨이에 보내고 게이트웨이가 서명 후 CPaws 로 포워딩.

해당 패턴은 generic `Anthropic` 으로 표현 불가 (옵션 없음) — 직접 코드 작성 필요.

## §G. CPaws-특이 파라미터 (`inference_geo` 등)

`inference_geo='us'` 등 CPaws-특이 request param 은 둘 다 **그냥 작동**.
`messages.create(...)` 가 kwargs 를 거의 그대로 JSON body 에 넣기 때문.

```python
# 두 SDK 모두 OK
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    inference_geo="us",                # ★ CPaws 전용
    messages=[...],
)
```

차이는 *type checker 우호도*. AnthropicAWS 쪽이 `inference_geo` 를 typed
schema 로 명시적으로 모델링하는 게 자연 (현재 0.96.0 에서는 둘 다 untyped — extra body
취급).

## §H. Async 변형

| 동기 | 비동기 |
|---|---|
| `Anthropic` | `AsyncAnthropic` |
| `AnthropicAWS` | `AsyncAnthropicAWS` |

본 프로젝트의 `tests/client/test_async.py` 는 현재 `AsyncAnthropicBedrock`
하드코딩. provider-aware 로 만들려면 `AsyncAnthropicAWS` 도 분기 추가 필요
(spec P4 항목).

## §I. 본 프로젝트의 두 경로 — 코드 차이

### Before (workaround)
```python
# providers/cpaws.py — replaced 2026-05-13
from anthropic import Anthropic

def make_client(region: str) -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    # ... presence checks ...
    return Anthropic(
        base_url=f"https://aws-external-anthropic.{region}.api.aws",
        api_key=api_key,
        default_headers={"anthropic-workspace-id": workspace_id},
    )
```

### After (공식 SDK)
```python
# providers/cpaws.py — current
from anthropic import AnthropicAWS

def make_client(region: str) -> AnthropicAWS:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    # ... presence checks ...
    return AnthropicAWS(
        api_key=api_key,
        workspace_id=workspace_id,
        aws_region=region,
    )
```

→ 의도가 더 명확. base_url 문자열 보일러플레이트 사라짐. 그리고 SDK 가
누락된 region/workspace 에 대해 더 일관된 에러 메시지 (`AnthropicError`)
를 제공.

## §J. 실측 결과 — 두 경로 동일한 contract 결과

CPaws / opus-4-7 / 57-test 풀스윗:

| 항목 | `Anthropic` workaround (2026-05-12) | `AnthropicAWS` (2026-05-13) |
|---|---|---|
| Overall result | 52/57 PASS | **52/57 PASS** |
| 카테고리별 결과 | 동일 | 동일 |
| 총 API calls | 62 | 62 |
| Input tokens | 286,097 | 286,088 |
| Output tokens | 2,575 | 2,482 |
| Cache create (1h) | 27,040 | 27,043 |
| Cache read | 125,944 | 125,949 |
| 총 청구 input | 538,508 | 538,509 |

→ wire-level 동일. 변화는 *클라이언트 측 구성 편의성* 만.

## §K. 사용 권장 매트릭스

| 시나리오 | 권장 |
|---|---|
| Production CPaws 호출 (SigV4 사용) | **AnthropicAWS** — SigV4 서명을 generic 으로 만들면 보일러플레이트 큼 |
| Production CPaws 호출 (API key 만) | **AnthropicAWS** 권장. workaround 도 작동하나 GA 후 마이그레이션 비용 |
| 다중 provider 추상화가 이미 있고 generic 클라이언트로 통일하고 싶음 | `Anthropic` workaround 또는 union type 으로 두 클래스 모두 수용 |
| 사내 LLM 게이트웨이 뒤에서 호출 (게이트웨이가 SigV4 처리) | **AnthropicAWS(skip_auth=True)** — generic 으로 표현 불가 |
| `claude.ai` / direct Anthropic API 와 코드 공유 | `Anthropic` (CPaws 만 다른 base_url 로 분기) |
| Beta 의존성을 회피하고 싶음 | `Anthropic` workaround (단 GA 후엔 AnthropicAWS 권장) |

## §L. 마이그레이션 체크리스트 (workaround → AnthropicAWS)

1. ✅ `from anthropic import AnthropicAWS` import 추가
2. ✅ 생성자 인자 변환:
   - `base_url=f"...{region}..."` 제거 → SDK 가 derive
   - `default_headers={"anthropic-workspace-id": ...}` 제거 → SDK 가 자동 주입
   - `workspace_id=` 인자 추가
   - `aws_region=` 인자 추가
3. ✅ 타입 어노테이션 `Anthropic` → `AnthropicAWS` (또는 `Anthropic | AnthropicAWS` union)
4. ✅ 풀스윗 회귀 테스트 (본 프로젝트: 52/57 동일 확인)
5. ☐ 의존성 매니페스트 — `anthropic` → `anthropic[aws]` (필요 시; 현재 anthropic 0.96.0 은 extras 없이도 import 됨)
6. ☐ Async 경로가 있다면 `AsyncAnthropic` → `AsyncAnthropicAWS` 분기
7. ☐ CI 환경의 SigV4 도입 검토 (workspace API key 의존성 줄이려면)

## §M. References

- 공식 docs: <https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws>
- SDK 소스: `anthropic/lib/aws/_client.py` (anthropic 0.96.0)
- 본 프로젝트 적용 commit: 2026-05-13 (이 문서의 commit 과 함께)
- 본 프로젝트 검증 baseline: `results/cpaws_findings.md` §A.6 (server tools)
