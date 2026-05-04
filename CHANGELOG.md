# Changelog

[![English](https://img.shields.io/badge/lang-English-blue.svg)](#english)
[![한국어](https://img.shields.io/badge/lang-한국어-red.svg)](#한국어)

---

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-05-03

### Added
- Add Claude Code project structure under `.claude/` with hooks (`session-context.sh`, `secret-scan.sh`, `check-doc-sync.sh`, `notify.sh`), skills (code-review, refactor, release, sync-docs), commands (review, test-all, deploy), and agents (code-reviewer, security-auditor)
- Add bilingual `docs/architecture.md` with full ASCII component diagram and data-flow summary
- Add `docs/onboarding.md` quickstart for new contributors
- Add `docs/decisions/ADR-001-cold-start-salt-for-cache-tests.md` recording the cold-start salt convention
- Add `docs/runbooks/refresh-matrix-baseline.md` runbook for periodic matrix snapshot
- Add module `CLAUDE.md` files for `tests/`, `scripts/`, `results/`, and `fixtures/`
- Add `tests/_meta/` harness self-validation suite with TAP-style runner, structure tests, and secret-pattern fixtures
- Add `scripts/setup.sh` and `scripts/install-hooks.sh` for new-developer onboarding and git hook installation
- Add `.env.example`, `.gitignore`, `.editorconfig` baseline configuration

### Changed
- Update root `CLAUDE.md` with Tech Stack, Conventions, Key Commands, and Auto-Sync Rules adapted to this verification suite
- Update `verify.sh` `usage()` and run wrappers to display per-run cost notice (~$5 USD per 3-model matrix)

## [0.5.0] - 2026-05-03

### Added
- Add `TokenAccumulator` and `wrap_client_with_tracker()` to `run_all.py` for per-call usage tracking via `messages.create` monkey-patch
- Add per-model and matrix-wide token usage summary printed at the end of every `run_all.py` invocation
- Add measured token cost notice to `verify.sh` header, `-h` output, and `run_all_tests` / `run_matrix` interactive functions

### Changed
- Track token usage in matrix mode using a fresh client per model, with both per-model and global accumulators wired via function chaining

## [0.4.0] - 2026-05-03

### Added
- Add `scripts/intercept_proxy.py` — local HTTP intercept proxy capturing Claude Code outbound traffic (cache_control breakpoints, TTL values, request body shapes)
- Add `scripts/probe_structured_outputs.py` — five-variant probe for structured outputs across three models in parallel
- Add `scripts/probe_token_counting.py` — three-path probe (Anthropic SDK, AWS-native CountTokens, Anthropic-shape) confirming the docs-vs-SDK layer split
- Add `results/claude_code_caching_findings.md` documenting Claude Code v2.1.126 wire-level emission for default, `ENABLE_PROMPT_CACHING_1H=1`, `DISABLE_PROMPT_CACHING=1`, and Mantle modes
- Add `results/docs_vs_reality.md` cross-walking every Anthropic docs claim against measured Bedrock contract

### Changed
- Reuse single `httpx.Client` across requests in `intercept_proxy.py` to preserve TLS session
- Hold log file descriptor open with line buffering instead of opening per request

## [0.3.0] - 2026-05-03

### Added
- Add `tests/messages/test_structured_outputs.py` encoding the model-divergent `output_config.format` contract (supported on Opus 4.6 / Sonnet 4.6, rejected on Opus 4.7 via Invoke API)
- Add `tests/tools/test_strict_tool_use.py` with the same model-divergent pattern for `tools[].strict=true`
- Add `usage_breakdown()` and `is_unsupported_tool_rejection()` helpers to `tests/_base.py` for shared cache-usage extraction and tool-type rejection matching
- Add `results/prompt_caching_verified.md` consolidated reference with TL;DR and claim-to-evidence mapping
- Add `results/structured_outputs_probe.json` and `results/token_counting_probe.json` raw probe captures

### Changed
- Rewrite `tests/messages/test_sampling_deprecated.py` as model-divergent (rejected_deprecated on Opus 4.7, supported_legacy on Opus 4.6 / Sonnet 4.6) using parallel API calls
- Rewrite `tests/tools/test_builtin_memory.py` as model-divergent (supported on Opus 4.6 / 4.7, rejected on Sonnet 4.6 due to schema gating)
- Broaden rejection-pattern matching in `tests/unsupported/test_computer_use_rejected.py` and `test_tool_search_rejected.py` to accept both "not supported" and "Input tag does not match" forms
- Update `tests/token_counting/test_count_tokens.py` to document the dual reality: Anthropic SDK rejects on Bedrock while AWS-native `CountTokens` API exists at `/model/{id}/count-tokens`

### Removed
- Remove `tests/unsupported/test_structured_outputs_rejected.py` — the test was sending OpenAI-style `response_format` instead of Anthropic's `output_config.format`, producing unknown-field errors that were misclassified as feature rejection
- Remove `tests/unsupported/test_strict_tool_use_rejected.py` — the test asserted blanket Bedrock rejection but Opus 4.6 / Sonnet 4.6 actually accept `strict=true`

### Fixed
- Fix `tests/unsupported/test_computer_use_rejected.py` matching against current SDK schema-validation error format
- Fix `tests/unsupported/test_tool_search_rejected.py` matching against current SDK schema-validation error format

## [0.2.0] - 2026-05-03

### Added
- Add `tests/caching/test_ttl_1h.py` verifying `ttl="1h"` populates `ephemeral_1h_input_tokens` on Bedrock without the rejected `extended-cache-ttl-2025-04-11` beta header
- Add `tests/caching/test_ttl_mixed.py` verifying mixed 5m + 1h request populates both buckets independently
- Add `results/variability_probe.py` — five cold-start trials demonstrating deterministic 1h cache support
- Add `results/stable_prefix_probe.py` — five stable-prefix trials demonstrating cache-state variance without salt

### Changed
- **BREAKING:** Reverse the cache TTL contract — earlier matrix asserted 1h was unsupported on Bedrock based on stale cache state; with cold-start salt, all three models populate the 1h bucket on fresh writes

### Fixed
- Fix false-positive cache TTL test results caused by stable prefix sharing state across runs

## [0.1.0] - 2026-05-03

### Added
- Add initial test harness in `tests/_base.py` with `Result` dataclass, `execute()` defensive runner, and `text_of()` helper
- Add `run_all.py` test discovery and execution runner with per-category summary and four-state classifier (supported / rejected / mixed / fail)
- Add `client.py` with `make_client()` factory reading `AWS_BEARER_TOKEN_BEDROCK`
- Add `config.py` with `MODEL_ID`, `REGION`, `ALL_MODELS`, and beta-header constants
- Add initial test categories: messages, streaming, token_counting, vision, documents, citations, tools, thinking, caching, context, multilingual, client, unsupported
- Add `verify.sh` interactive launcher with menu-based test selection
- Add `fixtures/red_4x4.png` and `fixtures/sample.pdf` for vision and document tests
- Add `docs/bedrock-api-endpoints-comparison.md` cataloging Bedrock's three service endpoints and five API patterns

[Unreleased]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/releases/tag/v0.1.0

---

# 한국어

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

## [0.6.0] - 2026-05-03

### Added
- `.claude/` 하위 Claude Code 프로젝트 구조 추가 — hooks(`session-context.sh`, `secret-scan.sh`, `check-doc-sync.sh`, `notify.sh`), skills(code-review, refactor, release, sync-docs), commands(review, test-all, deploy), agents(code-reviewer, security-auditor)
- 전체 ASCII 컴포넌트 다이어그램과 데이터 흐름 요약을 담은 이중 언어 `docs/architecture.md` 추가
- 신규 컨트리뷰터용 quickstart `docs/onboarding.md` 추가
- cold-start salt 컨벤션을 기록하는 `docs/decisions/ADR-001-cold-start-salt-for-cache-tests.md` 추가
- 주기적 매트릭스 스냅샷 절차서 `docs/runbooks/refresh-matrix-baseline.md` 추가
- `tests/`, `scripts/`, `results/`, `fixtures/` 모듈별 `CLAUDE.md` 추가
- TAP 스타일 러너, 구조 테스트, 시크릿 패턴 픽스처를 포함한 `tests/_meta/` 하네스 self-validation 스위트 추가
- 신규 개발자 온보딩 및 git hook 설치를 위한 `scripts/setup.sh`와 `scripts/install-hooks.sh` 추가
- `.env.example`, `.gitignore`, `.editorconfig` 기본 설정 추가

### Changed
- 본 검증 스위트에 맞춘 Tech Stack, Conventions, Key Commands, Auto-Sync Rules로 root `CLAUDE.md` 갱신
- 회당 비용 안내(3-모델 매트릭스 약 $5 USD)를 표시하도록 `verify.sh`의 `usage()` 및 실행 wrapper 갱신

## [0.5.0] - 2026-05-03

### Added
- `messages.create` monkey-patch를 통한 호출별 usage 추적용 `TokenAccumulator`와 `wrap_client_with_tracker()`를 `run_all.py`에 추가
- 모든 `run_all.py` 실행 종료 시 모델별 + 매트릭스 전체 토큰 사용량 요약 출력 추가
- `verify.sh` 헤더, `-h` 출력, `run_all_tests` / `run_matrix` 인터랙티브 함수에 측정된 토큰 비용 안내 추가

### Changed
- 매트릭스 모드에서 모델별 fresh client를 사용하고, 함수 체이닝을 통해 모델별 + 글로벌 누적기를 동시 연결하여 토큰 사용량 추적

## [0.4.0] - 2026-05-03

### Added
- Claude Code outbound 트래픽(cache_control breakpoint, TTL 값, 요청 body 형태)을 캡처하는 로컬 HTTP intercept proxy `scripts/intercept_proxy.py` 추가
- 3개 모델에 대한 5가지 구조화 출력 변형 병렬 probe `scripts/probe_structured_outputs.py` 추가
- docs와 SDK 레이어 분리를 확인하는 3-경로 probe(Anthropic SDK, AWS-native CountTokens, Anthropic-shape) `scripts/probe_token_counting.py` 추가
- Claude Code v2.1.126의 default, `ENABLE_PROMPT_CACHING_1H=1`, `DISABLE_PROMPT_CACHING=1`, Mantle 모드별 wire-level emission을 기록한 `results/claude_code_caching_findings.md` 추가
- Anthropic 공식 docs의 모든 claim을 실측 Bedrock contract와 대조하는 `results/docs_vs_reality.md` 추가

### Changed
- TLS 세션 보존을 위해 `intercept_proxy.py`의 요청 간 단일 `httpx.Client` 재사용
- 요청별 파일 open 대신 line-buffered 모드로 로그 파일 디스크립터 상시 보유

## [0.3.0] - 2026-05-03

### Added
- 모델별 분기 `output_config.format` contract(Opus 4.6 / Sonnet 4.6 지원, Opus 4.7 Invoke API 거부)를 인코딩하는 `tests/messages/test_structured_outputs.py` 추가
- `tools[].strict=true`에 대한 동일한 모델별 분기 패턴 `tests/tools/test_strict_tool_use.py` 추가
- 공유 캐시 사용량 추출 및 tool-type 거부 매칭을 위한 `usage_breakdown()`과 `is_unsupported_tool_rejection()` 헬퍼를 `tests/_base.py`에 추가
- TL;DR 표와 claim → evidence 매핑을 담은 종합 reference `results/prompt_caching_verified.md` 추가
- 원본 probe 캡처 `results/structured_outputs_probe.json`과 `results/token_counting_probe.json` 추가

### Changed
- `tests/messages/test_sampling_deprecated.py`를 모델별 분기(Opus 4.7은 rejected_deprecated, Opus 4.6 / Sonnet 4.6은 supported_legacy)로 재작성하면서 API 호출 병렬화
- `tests/tools/test_builtin_memory.py`를 모델별 분기(Opus 4.6 / 4.7 지원, 스키마 게이팅으로 인해 Sonnet 4.6 거부)로 재작성
- `tests/unsupported/test_computer_use_rejected.py`와 `test_tool_search_rejected.py`의 거부 패턴 매칭을 "not supported"와 "Input tag does not match" 두 형태 모두 수용하도록 확장
- `tests/token_counting/test_count_tokens.py`를 이중 현실(Anthropic SDK는 Bedrock 거부, AWS-native `CountTokens` API는 `/model/{id}/count-tokens`에 존재) 기준으로 갱신

### Removed
- `tests/unsupported/test_structured_outputs_rejected.py` 제거 — 해당 테스트가 Anthropic의 `output_config.format` 대신 OpenAI 식 `response_format`을 전송하여 알 수 없는 필드 오류를 기능 거부로 잘못 분류
- `tests/unsupported/test_strict_tool_use_rejected.py` 제거 — 해당 테스트는 Bedrock 일괄 거부를 단언했으나 Opus 4.6 / Sonnet 4.6은 실제로 `strict=true`를 수용

### Fixed
- 현재 SDK의 schema-validation 오류 형식과 매칭되도록 `tests/unsupported/test_computer_use_rejected.py` 수정
- 현재 SDK의 schema-validation 오류 형식과 매칭되도록 `tests/unsupported/test_tool_search_rejected.py` 수정

## [0.2.0] - 2026-05-03

### Added
- 거부되는 `extended-cache-ttl-2025-04-11` beta header 없이 `ttl="1h"`가 Bedrock의 `ephemeral_1h_input_tokens`를 채움을 검증하는 `tests/caching/test_ttl_1h.py` 추가
- 5m + 1h 혼합 요청이 두 버킷을 독립적으로 채움을 검증하는 `tests/caching/test_ttl_mixed.py` 추가
- 결정적 1h 캐시 지원을 입증하는 5회 cold-start 시도 `results/variability_probe.py` 추가
- salt 없는 캐시 상태 변동성을 입증하는 5회 stable-prefix 시도 `results/stable_prefix_probe.py` 추가

### Changed
- **BREAKING:** 캐시 TTL contract 반전 — 이전 매트릭스는 stale 캐시 상태에 근거해 1h가 Bedrock에서 미지원이라고 단언했으나, cold-start salt 적용 시 3개 모델 모두 fresh write에서 1h 버킷이 채워짐

### Fixed
- 실행 간 상태를 공유하는 stable prefix가 유발하던 캐시 TTL 테스트의 false-positive 결과 수정

## [0.1.0] - 2026-05-03

### Added
- `Result` dataclass, `execute()` 방어적 러너, `text_of()` 헬퍼를 포함한 초기 테스트 하네스 `tests/_base.py` 추가
- 카테고리별 요약과 4상태 분류기(supported / rejected / mixed / fail)를 갖춘 `run_all.py` 테스트 발견·실행 러너 추가
- `AWS_BEARER_TOKEN_BEDROCK`을 읽는 `make_client()` 팩토리 `client.py` 추가
- `MODEL_ID`, `REGION`, `ALL_MODELS`, beta-header 상수를 담은 `config.py` 추가
- 초기 테스트 카테고리(messages, streaming, token_counting, vision, documents, citations, tools, thinking, caching, context, multilingual, client, unsupported) 추가
- 메뉴 기반 테스트 선택을 제공하는 인터랙티브 launcher `verify.sh` 추가
- 비전 및 문서 테스트용 `fixtures/red_4x4.png`와 `fixtures/sample.pdf` 추가
- Bedrock의 3개 서비스 엔드포인트와 5가지 API 패턴을 정리한 `docs/bedrock-api-endpoints-comparison.md` 추가

[Unreleased]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/whchoi98/bedrock-claude-contract-suite/releases/tag/v0.1.0
