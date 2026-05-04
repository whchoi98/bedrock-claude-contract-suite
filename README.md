# bedrock-claude-contract-suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#testing)
[![Version](https://img.shields.io/badge/version-0.6.0-blue.svg)](CHANGELOG.md)
[![English](https://img.shields.io/badge/lang-English-blue.svg)](#english)
[![한국어](https://img.shields.io/badge/lang-한국어-red.svg)](#한국어)

A categorized contract verification suite for the Anthropic Messages API on Amazon Bedrock — empirical, model-divergent, evidence-cited.

Amazon Bedrock에서 호스팅되는 Anthropic Messages API의 카테고리별 contract 검증 스위트 — 실측 기반, 모델별 분기 인코딩, 증거 추적.

---

# English

## Overview

`bedrock-claude-contract-suite` encodes the runtime API contract of Anthropic Claude models hosted on Amazon Bedrock as a deterministic test matrix. Each feature surface (caching, tools, thinking, vision, etc.) is captured as a categorized test that returns one of four states — supported, rejected, mixed, or fail — across multiple models in `ap-northeast-2`. The suite targets the `bedrock-runtime` InvokeModel API only; `bedrock-mantle` is intentionally out of scope.

## Features

- **Categorized matrix** — 57 tests across 13 categories (caching, messages, tools, thinking, vision, documents, citations, streaming, token_counting, context, multilingual, client, unsupported) executed against three models (Opus 4.7 / Opus 4.6 / Sonnet 4.6).
- **Cold-start cache verification** — every cache test injects a `secrets.token_hex(8)` salt to force fresh writes, eliminating false positives from shared cache state across runs (see ADR-001).
- **Wire-level Claude Code capture** — a local intercept proxy records the actual outbound HTTP that `claude` emits to Bedrock, including `cache_control` shapes, TTL values, and breakpoint locations.
- **Docs vs reality diff** — the `results/docs_vs_reality.md` reference cross-walks every Anthropic public docs claim against measured Bedrock behavior, distinguishing real discrepancies from documentation nuance.
- **Token cost tracking** — `run_all.py` accumulates per-call usage (input / output / cache create 5m / cache create 1h / cache reads) and prints a per-model and matrix-wide summary at the end of every run.

## Prerequisites

- Python 3.9 or later
- AWS account with Amazon Bedrock model access for `global.anthropic.claude-opus-4-7`, `global.anthropic.claude-opus-4-6-v1`, and `global.anthropic.claude-sonnet-4-6` in the `ap-northeast-2` region
- An Amazon Bedrock API key (Bearer token) issued from the Bedrock console
- Python packages: `anthropic`, `httpx`, `boto3`

## Installation

```bash
# Clone the repository
git clone https://github.com/whchoi98/bedrock-claude-contract-suite.git
cd bedrock-claude-contract-suite

# Install Python dependencies
pip install anthropic httpx boto3

# Copy environment template and fill in your Bedrock API key
cp .env.example .env
# Edit .env — set AWS_BEARER_TOKEN_BEDROCK to your real key

# Run the new-developer setup script (idempotent)
bash scripts/setup.sh
```

## Usage

```bash
# Source environment variables
source .env

# Run a single-model verification (uses BEDROCK_MODEL_ID, default Opus 4.7)
python3 run_all.py
# Output: results/latest.{json,md} + token usage summary

# Run the full 3-model matrix (~$5 USD per run, ~3 minutes)
python3 run_all.py --all-models
# Output: results/matrix.{json,md} + per-model + matrix-wide token summary

# Filter by category or test name
python3 run_all.py --only caching tools
python3 run_all.py --only-tests cache_ttl_1h

# Interactive launcher with cost notice
./verify.sh
./verify.sh -h    # show cost estimates
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API key (Bearer token), required | — |
| `AWS_REGION` | AWS region for the Bedrock endpoint | `ap-northeast-2` |
| `BEDROCK_MODEL_ID` | Single-model run target (ignored in `--all-models` mode) | `global.anthropic.claude-opus-4-7` |
| `CLAUDE_NOTIFY_WEBHOOK` | Optional webhook URL for the `notify.sh` Claude Code hook | empty (disabled) |

## Project Structure

```
bedrock-claude-contract-suite/
├── config.py                  # MODEL_ID, REGION, ALL_MODELS, beta-header constants
├── client.py                  # make_client() — AnthropicBedrock factory
├── run_all.py                 # discover, execute, classify, print token summary
├── verify.sh                  # interactive launcher with cost notice
├── tests/                     # contract suite
│   ├── _base.py               # Result, execute, text_of, usage_breakdown,
│   │                          #   is_unsupported_tool_rejection
│   └── <category>/test_*.py   # NAME / DESCRIPTION / run(client, model)
├── scripts/                   # one-off probes and the intercept proxy
│   ├── intercept_proxy.py     # captures Claude Code outbound HTTP
│   └── probe_*.py             # ad-hoc API contract probes
├── results/                   # generated artifacts + verified findings
│   ├── latest.{json,md}       # single-model run output
│   ├── matrix.{json,md}       # 3-model matrix output
│   ├── prompt_caching_verified.md   # caching contract reference
│   └── docs_vs_reality.md     # docs vs measured contract diff
├── docs/
│   ├── architecture.md        # system architecture (KR/EN)
│   ├── bedrock-api-endpoints-comparison.md
│   ├── decisions/             # Architecture Decision Records
│   └── runbooks/              # operational runbooks
├── fixtures/                  # vision / PDF test inputs
├── .claude/                   # hooks, skills, commands, agents
└── tests/_meta/               # harness self-validation tests
```

## Testing

```bash
# Run the full contract matrix against Bedrock
python3 run_all.py --all-models

# Run a single category
python3 run_all.py --only caching

# Validate the harness itself (hooks, structure, secret patterns)
bash tests/_meta/run-all.sh

# Filter meta-tests by area
bash tests/_meta/run-all.sh hooks
bash tests/_meta/run-all.sh structure
```

## API Documentation

Authoritative references for understanding the Bedrock surface this suite exercises:

- [`docs/architecture.md`](docs/architecture.md) — system architecture, components, data flow
- [`docs/bedrock-api-endpoints-comparison.md`](docs/bedrock-api-endpoints-comparison.md) — Bedrock's three service endpoints and five API patterns
- [`results/prompt_caching_verified.md`](results/prompt_caching_verified.md) — caching contract reference with claim-to-evidence mapping
- [`results/docs_vs_reality.md`](results/docs_vs_reality.md) — Anthropic public docs versus measured Bedrock contract
- [`docs/onboarding.md`](docs/onboarding.md) — quickstart for new contributors

## Contributing

1. Fork the repository at https://github.com/whchoi98/bedrock-claude-contract-suite
2. Create a feature branch from `main` — `git checkout -b feat/your-change`
3. Commit your changes following Conventional Commits — `git commit -m "feat: add <category> test for <feature>"`
4. Push to your fork — `git push origin feat/your-change`
5. Open a pull request to `main` describing the contract change and linking the relevant test or probe output

Commit message examples:

```text
feat: add tests/caching/test_ttl_24h.py for extended cache window
fix: narrow except in scripts/probe_token_counting.py to httpx.HTTPError
docs: update docs_vs_reality.md after Bedrock structured outputs GA
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Contact

- Maintainer: [@whchoi98](https://github.com/whchoi98) — whchoi98@gmail.com
- Issues: https://github.com/whchoi98/bedrock-claude-contract-suite/issues
- Pull requests: https://github.com/whchoi98/bedrock-claude-contract-suite/pulls

---

# 한국어

## 개요

`bedrock-claude-contract-suite`는 Amazon Bedrock에서 호스팅되는 Anthropic Claude 모델의 런타임 API contract를 결정적 테스트 매트릭스로 인코딩합니다. 각 기능 surface(캐싱, 도구, thinking, 비전 등)를 카테고리별 테스트로 캡처해 `ap-northeast-2` 리전의 여러 모델에 대해 supported / rejected / mixed / fail 4상태 결과를 생성합니다. 검증 범위는 `bedrock-runtime`의 InvokeModel API 경로뿐이며 `bedrock-mantle`은 의도적으로 scope 밖입니다.

## 주요 기능

- **카테고리별 매트릭스** — 13개 카테고리(caching, messages, tools, thinking, vision, documents, citations, streaming, token_counting, context, multilingual, client, unsupported) 57개 테스트를 3개 모델(Opus 4.7 / Opus 4.6 / Sonnet 4.6)에 대해 실행합니다.
- **Cold-start 캐시 검증** — 모든 캐시 테스트는 `secrets.token_hex(8)` salt를 주입해 fresh write를 강제하므로 이전 실행의 캐시 상태로 인한 false positive가 제거됩니다 (ADR-001 참조).
- **Claude Code wire-level 캡처** — 로컬 intercept 프록시가 `claude`가 Bedrock으로 실제 보내는 outbound HTTP를 기록합니다(cache_control 형태, TTL 값, breakpoint 위치 포함).
- **Docs vs reality 비교** — `results/docs_vs_reality.md`가 Anthropic 공식 docs의 모든 claim을 실측 Bedrock 동작과 대조해 진짜 불일치와 문서 nuance를 구분해 정리합니다.
- **토큰 비용 추적** — `run_all.py`가 호출별 usage(input / output / cache create 5m / cache create 1h / cache reads)를 누적해 매 실행 종료 시 모델별 + 매트릭스 전체 요약을 출력합니다.

## 사전 요구 사항

- Python 3.9 이상
- `ap-northeast-2` 리전에서 `global.anthropic.claude-opus-4-7`, `global.anthropic.claude-opus-4-6-v1`, `global.anthropic.claude-sonnet-4-6` 모델 접근이 활성화된 AWS 계정
- Bedrock 콘솔에서 발급한 Amazon Bedrock API key (Bearer token)
- Python 패키지: `anthropic`, `httpx`, `boto3`

## 설치 방법

```bash
# 저장소 클론
git clone https://github.com/whchoi98/bedrock-claude-contract-suite.git
cd bedrock-claude-contract-suite

# Python 의존성 설치
pip install anthropic httpx boto3

# 환경 변수 템플릿 복사 후 Bedrock API key 입력
cp .env.example .env
# .env 편집 — AWS_BEARER_TOKEN_BEDROCK에 실제 키 입력

# 신규 컨트리뷰터용 setup 스크립트 실행 (멱등)
bash scripts/setup.sh
```

## 사용법

```bash
# 환경 변수 로드
source .env

# 단일 모델 검증 실행 (BEDROCK_MODEL_ID 사용, 기본값 Opus 4.7)
python3 run_all.py
# 출력: results/latest.{json,md} + 토큰 사용량 요약

# 3-모델 매트릭스 실행 (회당 약 $5 USD, 약 3분 소요)
python3 run_all.py --all-models
# 출력: results/matrix.{json,md} + 모델별 + 매트릭스 전체 토큰 요약

# 카테고리 또는 테스트 이름으로 필터링
python3 run_all.py --only caching tools
python3 run_all.py --only-tests cache_ttl_1h

# 비용 안내가 포함된 인터랙티브 launcher
./verify.sh
./verify.sh -h    # 비용 추정치 표시
```

## 환경 설정

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API key (Bearer token), 필수 | — |
| `AWS_REGION` | Bedrock 엔드포인트의 AWS 리전 | `ap-northeast-2` |
| `BEDROCK_MODEL_ID` | 단일 모델 실행 대상 (`--all-models` 모드에서는 무시) | `global.anthropic.claude-opus-4-7` |
| `CLAUDE_NOTIFY_WEBHOOK` | `notify.sh` Claude Code hook용 선택적 webhook URL | 빈 값 (비활성) |

## 프로젝트 구조

```
bedrock-claude-contract-suite/
├── config.py                  # MODEL_ID, REGION, ALL_MODELS, beta-header 상수
├── client.py                  # make_client() — AnthropicBedrock 팩토리
├── run_all.py                 # discover, execute, classify, 토큰 요약 출력
├── verify.sh                  # 비용 안내 포함 인터랙티브 launcher
├── tests/                     # contract 스위트
│   ├── _base.py               # Result, execute, text_of, usage_breakdown,
│   │                          #   is_unsupported_tool_rejection
│   └── <category>/test_*.py   # NAME / DESCRIPTION / run(client, model)
├── scripts/                   # 일회성 probe 및 intercept proxy
│   ├── intercept_proxy.py     # Claude Code outbound HTTP 캡처
│   └── probe_*.py             # ad-hoc API contract 탐사
├── results/                   # 생성 산출물 + 검증된 finding
│   ├── latest.{json,md}       # 단일 모델 실행 결과
│   ├── matrix.{json,md}       # 3-모델 매트릭스 결과
│   ├── prompt_caching_verified.md   # 캐싱 contract reference
│   └── docs_vs_reality.md     # docs 대비 실측 contract diff
├── docs/
│   ├── architecture.md        # 시스템 아키텍처 (KR/EN)
│   ├── bedrock-api-endpoints-comparison.md
│   ├── decisions/             # Architecture Decision Records
│   └── runbooks/              # 운영 절차서
├── fixtures/                  # 비전 / PDF 테스트 입력
├── .claude/                   # hooks, skills, commands, agents
└── tests/_meta/               # 하네스 self-validation 테스트
```

## 테스트

```bash
# Bedrock에 대해 전체 contract 매트릭스 실행
python3 run_all.py --all-models

# 단일 카테고리 실행
python3 run_all.py --only caching

# 하네스 자체 검증 (hooks, 구조, 시크릿 패턴)
bash tests/_meta/run-all.sh

# 영역별 메타-테스트 필터
bash tests/_meta/run-all.sh hooks
bash tests/_meta/run-all.sh structure
```

## API 문서

본 스위트가 검증하는 Bedrock surface를 이해하기 위한 권위 있는 reference:

- [`docs/architecture.md`](docs/architecture.md) — 시스템 아키텍처, 컴포넌트, 데이터 흐름
- [`docs/bedrock-api-endpoints-comparison.md`](docs/bedrock-api-endpoints-comparison.md) — Bedrock의 3개 서비스 엔드포인트 및 5가지 API 패턴
- [`results/prompt_caching_verified.md`](results/prompt_caching_verified.md) — 캐싱 contract reference (claim → evidence 매핑)
- [`results/docs_vs_reality.md`](results/docs_vs_reality.md) — Anthropic 공식 docs 대비 실측 Bedrock contract
- [`docs/onboarding.md`](docs/onboarding.md) — 신규 컨트리뷰터 quickstart

## 기여 방법

1. https://github.com/whchoi98/bedrock-claude-contract-suite 에서 저장소를 fork 합니다.
2. `main`에서 feature branch를 생성합니다 — `git checkout -b feat/your-change`
3. Conventional Commits 형식으로 커밋합니다 — `git commit -m "feat: add <category> test for <feature>"`
4. fork에 push 합니다 — `git push origin feat/your-change`
5. `main`을 대상으로 pull request를 열고 contract 변경 사항과 관련 테스트/probe 출력을 링크합니다.

커밋 메시지 예시:

```text
feat: add tests/caching/test_ttl_24h.py for extended cache window
fix: narrow except in scripts/probe_token_counting.py to httpx.HTTPError
docs: update docs_vs_reality.md after Bedrock structured outputs GA
```

## 라이선스

본 프로젝트는 MIT 라이선스 하에 배포됩니다 — 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하시기 바랍니다.

## 연락처

- 메인테이너: [@whchoi98](https://github.com/whchoi98) — whchoi98@gmail.com
- Issues: https://github.com/whchoi98/bedrock-claude-contract-suite/issues
- Pull requests: https://github.com/whchoi98/bedrock-claude-contract-suite/pulls

<!-- harness-eval-badge:start -->
![Harness Score](https://img.shields.io/badge/harness-8.0%2F10-green)
![Harness Grade](https://img.shields.io/badge/grade-A-green)
![Last Eval](https://img.shields.io/badge/eval-2026--05--03-blue)
<!-- harness-eval-badge:end -->
