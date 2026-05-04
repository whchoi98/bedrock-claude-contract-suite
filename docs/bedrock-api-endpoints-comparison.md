# Amazon Bedrock API 엔드포인트 비교 가이드

> 작성일: 2026-05-03  
> 참고: [AWS 공식 문서 - Endpoints supported by Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html)

---

## 목차

1. [개요](#1-개요)
2. [엔드포인트 구조](#2-엔드포인트-구조)
3. [API별 상세 비교](#3-api별-상세-비교)
4. [엔드포인트별 지원 API 매트릭스](#4-엔드포인트별-지원-api-매트릭스)
5. [엔드포인트별 기능 차이](#5-엔드포인트별-기능-차이)
6. [모델별 엔드포인트 가용성](#6-모델별-엔드포인트-가용성)
7. [인증 방식](#7-인증-방식)
8. [코드 예시](#8-코드-예시)
9. [선택 가이드](#9-선택-가이드)

---

## 1. 개요

Amazon Bedrock은 **세 가지 서비스 엔드포인트**를 제공한다:

| 엔드포인트 | URL 형식 | 용도 |
|-----------|----------|------|
| `bedrock` | `bedrock.{region}.amazonaws.com` | **컨트롤 플레인** — 모델 목록 조회, 커스텀 모델 작업, 프로비저닝된 처리량 관리 |
| `bedrock-runtime` | `bedrock-runtime.{region}.amazonaws.com` | **추론 (네이티브)** — Invoke, Converse, Chat Completions, Messages API |
| `bedrock-mantle` | `bedrock-mantle.{region}.api.aws` | **추론 (OpenAI 호환)** — Responses, Chat Completions, Messages API |

추론 엔드포인트는 `bedrock-runtime`과 `bedrock-mantle` 두 가지이며, 총 **5가지 API 패턴**을 지원한다.

### Project Mantle이란?

**Project Mantle**은 AWS가 개발한 **대규모 ML 모델 서빙을 위한 분산 추론 엔진**이다. 이 엔진 위에 OpenAI 호환 API를 제공하여, 기존 OpenAI SDK 코드를 `base_url`과 `api_key`만 변경하면 Bedrock에서 그대로 사용할 수 있다.

---

## 2. 엔드포인트 구조

```
Amazon Bedrock
├── bedrock (컨트롤 플레인)
│   └── bedrock.{region}.amazonaws.com
│
├── bedrock-runtime (네이티브 추론)
│   ├── Invoke API
│   ├── Converse API
│   ├── Chat Completions API
│   └── Messages API (Anthropic)
│
└── bedrock-mantle (OpenAI 호환 추론)
    ├── Responses API        ← AWS 최신 권장
    ├── Chat Completions API ← 권장 엔드포인트
    └── Messages API (Anthropic)
```

### bedrock-mantle 가용 리전

| 리전 | 엔드포인트 |
|------|-----------|
| US East (N. Virginia) | `bedrock-mantle.us-east-1.api.aws` |
| US East (Ohio) | `bedrock-mantle.us-east-2.api.aws` |
| US West (Oregon) | `bedrock-mantle.us-west-2.api.aws` |
| Asia Pacific (Tokyo) | `bedrock-mantle.ap-northeast-1.api.aws` |
| Asia Pacific (Mumbai) | `bedrock-mantle.ap-south-1.api.aws` |
| Asia Pacific (Sydney) | `bedrock-mantle.ap-southeast-2.api.aws` |
| Asia Pacific (Jakarta) | `bedrock-mantle.ap-southeast-3.api.aws` |
| Europe (Frankfurt) | `bedrock-mantle.eu-central-1.api.aws` |
| Europe (Ireland) | `bedrock-mantle.eu-west-1.api.aws` |
| Europe (London) | `bedrock-mantle.eu-west-2.api.aws` |
| Europe (Milan) | `bedrock-mantle.eu-south-1.api.aws` |
| Europe (Stockholm) | `bedrock-mantle.eu-north-1.api.aws` |
| South America (São Paulo) | `bedrock-mantle.sa-east-1.api.aws` |

---

## 3. API별 상세 비교

### 3.1 Responses API (bedrock-mantle) — 최신 권장

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `bedrock-mantle.{region}.api.aws/v1/responses` |
| 상태 관리 | **Stateful** — 대화 히스토리를 서버에서 자동 관리 |
| 스트리밍 | 지원 (`stream: true`) |
| Tool Use | 내장 도구 (검색, 코드 인터프리터) + 커스텀 도구 |
| 비동기 추론 | 지원 (장시간 실행 워크로드) |
| 멀티모달 | 지원 |
| SDK 호환 | OpenAI SDK 직접 사용 가능 |
| 적합한 용도 | 에이전트/agentic 워크플로우, 새 프로젝트 |

### 3.2 Chat Completions API (bedrock-mantle 권장 / bedrock-runtime 지원)

| 항목 | 내용 |
|------|------|
| 엔드포인트 (권장) | `bedrock-mantle.{region}.api.aws/v1/chat/completions` |
| 엔드포인트 (대체) | `bedrock-runtime.{region}.amazonaws.com` |
| 상태 관리 | **Stateless** — 매 요청마다 전체 대화 히스토리 전송 필요 |
| 스트리밍 | 지원 (`stream: true`) |
| Tool Use | 지원 (function calling) |
| SDK 호환 | OpenAI SDK 직접 사용 가능 |
| 적합한 용도 | OpenAI에서 마이그레이션, 경량 텍스트 중심 작업, 낮은 레이턴시 |

### 3.3 Messages API (bedrock-mantle / bedrock-runtime)

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `bedrock-mantle.{region}.api.aws` 또는 `bedrock-runtime` |
| 요청 형식 | **Anthropic 네이티브** (`anthropic_version`, `messages` 형식) |
| 상태 관리 | Stateless |
| 스트리밍 | 지원 |
| Tool Use | 지원 |
| Extended Thinking | 지원 (Claude 3.7+) |
| 멀티모달 | 이미지, 문서 입력 지원 |
| 적합한 용도 | Anthropic Claude 모델 전용 기능 활용 (extended thinking, adaptive thinking 등) |

### 3.4 Converse API (bedrock-runtime)

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `bedrock-runtime.{region}.amazonaws.com` |
| API 경로 | `POST /model/{modelId}/converse` |
| 요청 형식 | **통합 형식** — 모든 Bedrock 모델에 동일한 인터페이스 |
| 상태 관리 | Stateless |
| 스트리밍 | `ConverseStream` 별도 API |
| Tool Use | 내장 지원 (클라이언트 사이드) |
| 가드레일 | 내장 지원 |
| 멀티모달 | 이미지, 문서, 비디오 입력 표준화 |
| 적합한 용도 | 모델 간 전환이 잦은 경우, 모든 Bedrock 모델 통합 사용 |

### 3.5 InvokeModel API (bedrock-runtime)

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `bedrock-runtime.{region}.amazonaws.com` |
| API 경로 | `POST /model/{modelId}/invoke` |
| 요청 형식 | **모델별 네이티브 형식** — 모델마다 body 구조가 다름 |
| 상태 관리 | Stateless (단일 요청/응답) |
| 스트리밍 | `InvokeModelWithResponseStream` 별도 API |
| 출력 타입 | 텍스트, 이미지, 임베딩 |
| 가드레일 | 수동 설정 (guardrailIdentifier 파라미터) |
| 적합한 용도 | 임베딩 생성, 이미지 생성, 모델 고유 파라미터 세밀 제어 |

---

## 4. 엔드포인트별 지원 API 매트릭스

| API | `bedrock-mantle` | `bedrock-runtime` |
|-----|:----------------:|:-----------------:|
| Responses API | ✅ | ❌ |
| Chat Completions API | ✅ (권장) | ✅ |
| Messages API (Anthropic) | ✅ | ✅ |
| Converse API | ❌ | ✅ |
| InvokeModel API | ❌ | ✅ |

---

## 5. 엔드포인트별 기능 차이

| 기능 | `bedrock-mantle` | `bedrock-runtime` |
|------|:----------------:|:-----------------:|
| OpenAI SDK 호환 | ✅ | ❌ |
| Bedrock API Key 인증 | ✅ | ❌ |
| AWS 자격증명 인증 | ✅ | ✅ |
| 서버 사이드 Tool Use | ✅ | ❌ |
| 클라이언트 사이드 Tool Use | ✅ | ✅ |
| 내장 도구 (검색, 코드 인터프리터) | ✅ | ❌ |
| 사용량/비용 추적 | ❌ | ✅ |
| 가드레일 | API별 상이 | Converse 내장 지원 |
| Stateful 대화 | ✅ (Responses API) | ❌ |
| 비동기 추론 | ✅ (Responses API) | ❌ |

---

## 6. 모델별 엔드포인트 가용성

### 양쪽 엔드포인트 모두 지원하는 모델

| 프로바이더 | 모델 |
|-----------|------|
| Anthropic | Claude Haiku 4.5, Claude Opus 4.7, Claude Mythos Preview (mantle only) |
| DeepSeek | DeepSeek V3.1, DeepSeek V3.2 |
| Google | Gemma 3 4B/12B/27B |
| MiniMax | M2, M2.1, M2.5 |
| Mistral AI | Mistral Large 3, Devstral 2, Magistral Small, Ministral 시리즈 |
| Moonshot AI | Kimi K2 Thinking, Kimi K2.5 |
| NVIDIA | Nemotron Nano/Super 시리즈 |
| OpenAI | GPT OSS 120B, GPT OSS 20B (+ Safeguard 버전) |
| Qwen | Qwen3 32B, Qwen3 235B, Qwen3 Coder 시리즈, Qwen3 VL |
| Writer | Palmyra Vision 7B |
| Z.AI | GLM 4.7, GLM 4.7 Flash, GLM 5 |

### bedrock-runtime 전용 모델 (bedrock-mantle 미지원)

| 프로바이더 | 모델 |
|-----------|------|
| AI21 Labs | Jamba 1.5 Large/Mini |
| Amazon | Nova 시리즈 전체, Titan 시리즈 전체 |
| Anthropic | Claude 3 Haiku, Claude 3.5 Haiku, Claude Opus 4.1/4.5/4.6, Claude Sonnet 4/4.5/4.6 |
| Cohere | Command R/R+, Embed 시리즈, Rerank |
| Meta | Llama 3/3.1/3.2/3.3/4 전체 |
| Stability AI | Stable Image 시리즈 전체 |
| TwelveLabs | Marengo Embed, Pegasus |

> **참고**: 임베딩 모델, 이미지 생성 모델, 비디오 모델은 `bedrock-runtime`에서만 사용 가능하다.

---

## 7. 인증 방식

### bedrock-mantle

두 가지 인증 방식을 지원한다:

1. **Bedrock API Key** (장기 키) — OpenAI SDK 사용 시 필수
   ```bash
   export OPENAI_API_KEY="<Bedrock API Key>"
   export OPENAI_BASE_URL="https://bedrock-mantle.us-east-1.api.aws/v1"
   ```

2. **AWS 자격증명** — HTTP 요청 시 SigV4 서명 사용

### bedrock-runtime

- **AWS 자격증명만 지원** — IAM 역할, 액세스 키, 임시 자격증명 등
- boto3 등 AWS SDK를 통해 자동 인증

---

## 8. 코드 예시

### 8.1 Responses API (bedrock-mantle) — OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://bedrock-mantle.us-east-1.api.aws/v1",
    api_key="<Bedrock API Key>"
)

# 기본 요청
response = client.responses.create(
    model="anthropic.claude-opus-4-7-v1:0",
    input=[{"role": "user", "content": "안녕하세요!"}]
)
print(response)

# 스트리밍
stream = client.responses.create(
    model="anthropic.claude-opus-4-7-v1:0",
    input=[{"role": "user", "content": "이야기를 들려주세요"}],
    stream=True
)
for event in stream:
    print(event)
```

### 8.2 Chat Completions API (bedrock-mantle) — OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://bedrock-mantle.us-east-1.api.aws/v1",
    api_key="<Bedrock API Key>"
)

completion = client.chat.completions.create(
    model="anthropic.claude-opus-4-7-v1:0",
    messages=[
        {"role": "system", "content": "당신은 유용한 어시스턴트입니다."},
        {"role": "user", "content": "안녕하세요!"}
    ]
)
print(completion.choices[0].message)
```

### 8.3 Converse API (bedrock-runtime) — boto3

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.converse(
    modelId="anthropic.claude-sonnet-4-20250514-v1:0",
    messages=[
        {
            "role": "user",
            "content": [{"text": "안녕하세요!"}]
        }
    ],
    inferenceConfig={"maxTokens": 1024, "temperature": 0.7}
)

print(response["output"]["message"]["content"][0]["text"])
```

### 8.4 InvokeModel API (bedrock-runtime) — boto3

```python
import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "안녕하세요!"}
    ]
})

response = client.invoke_model(
    modelId="anthropic.claude-sonnet-4-20250514-v1:0",
    body=body
)

result = json.loads(response["body"].read())
print(result["content"][0]["text"])
```

### 8.5 Messages API (bedrock-mantle) — curl

```bash
curl -X POST "https://bedrock-mantle.us-east-1.api.aws/v1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "anthropic.claude-opus-4-7-v1:0",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "안녕하세요!"}
    ]
  }'
```

---

## 9. 선택 가이드

### 유스케이스별 권장 API

| 유스케이스 | 권장 API | 이유 |
|-----------|---------|------|
| 새 프로젝트 시작 | **Responses API** (bedrock-mantle) | AWS 최신 권장, stateful 대화, 내장 도구 |
| OpenAI에서 마이그레이션 | **Chat Completions** 또는 **Responses API** (bedrock-mantle) | base_url만 변경하면 동작 |
| Anthropic Claude 전용 기능 | **Messages API** | Extended thinking, adaptive thinking 등 |
| 모든 모델 통합 인터페이스 | **Converse API** (bedrock-runtime) | 코드 한 번 작성으로 모든 모델 사용 |
| 임베딩/이미지 생성 | **InvokeModel** (bedrock-runtime) | 텍스트 외 출력은 Invoke만 지원 |
| 모델 고유 파라미터 세밀 제어 | **InvokeModel** (bedrock-runtime) | 모델 네이티브 형식 직접 사용 |
| 비용/사용량 추적 필요 | **Converse/Invoke** (bedrock-runtime) | bedrock-runtime에서 사용량 추적 지원 |

### 의사결정 플로우차트

```
OpenAI SDK를 사용하고 싶은가?
├── Yes → bedrock-mantle
│   ├── Stateful 대화/에이전트가 필요한가?
│   │   ├── Yes → Responses API
│   │   └── No → Chat Completions API
│   └── Anthropic 네이티브 형식이 필요한가?
│       └── Yes → Messages API
│
└── No → bedrock-runtime
    ├── 모든 모델에 통일된 인터페이스가 필요한가?
    │   └── Yes → Converse API
    └── 임베딩/이미지 생성 또는 모델별 세밀 제어가 필요한가?
        └── Yes → InvokeModel API
```

---

## 참고 링크

- [Endpoints supported by Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html)
- [APIs supported by Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/apis.html)
- [Generate responses using OpenAI APIs (Mantle)](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html)
- [Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [InvokeModel API](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-invoke.html)
- [Endpoint availability (모델별)](https://docs.aws.amazon.com/bedrock/latest/userguide/models-endpoint-availability.html)
- [Anthropic Claude Messages API](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)
