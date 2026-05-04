# Bedrock × Anthropic Messages API verification

- **Started (UTC)**: 2026-05-03T10:40:18Z
- **Region**: `ap-northeast-2`
- **Model**: `global.anthropic.claude-opus-4-7`
- **Result**: **8 / 8 passed**

## Result legend

| Icon | Meaning | Count |
| --- | --- | ---: |
| 🟢 | **Supported** — feature works on Bedrock; behavior verified | 7 |
| ⛔ | **Rejected (contract)** — feature is NOT supported on Bedrock; rejection verified | 1 |
| 🟡 | **Mixed** — partial support (e.g. header accepted, config rejected) | 0 |
| ❌ | **FAIL** — actual failure | 0 |

**Genuine feature support on this model+region**: 7 of 8 surfaces. 1 surfaces are confirmed unsupported. 0 are partially supported.

## Summary by category

| Category | Total | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail |
| --- | ---: | ---: | ---: | ---: | ---: |
| `caching` | 8 | 7 | 1 | 0 | 0 |

## Details

### `caching` — 8 / 8

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `extended_ttl_beta_header_rejected_on_bedrock` | ⛔ REJECTED (contract) | 1.69s | anthropic-beta: extended-cache-ttl-2025-04-11 is rejected on Bedrock | {"contract": "rejected", "message": "Error code: 400 - {'message': 'invalid beta flag'}"} |
| `cache_multi_breakpoint` | 🟢 SUPPORTED (behavior verified) | 4.75s | system breakpoint AND user message breakpoint both register | {"first": {"input": 21, "create": 0, "read": 19507}, "second": {"input": 21, "create": 0, "read": 19507}, "path": "hot"} |
| `cache_on_messages` | 🟢 SUPPORTED (behavior verified) | 4.30s | cache_control on a user content block triggers cache create/read | {"first": {"input": 25, "create": 0, "read": 10005}, "second": {"input": 25, "create": 0, "read": 10005}, "path": "hot"} |
| `prompt_caching` | 🟢 SUPPORTED (behavior verified) | 4.81s | cache_control marks a system prefix; 2nd call shows cache_read_input_tokens | {"first_call_usage": {"input_tokens": 22, "output_tokens": 11, "cache_creation_input_tokens": 0, "cache_read_input_token |
| `cache_on_tools` | 🟢 SUPPORTED (behavior verified) | 5.68s | cache_control attached to last tool definition triggers cache use | {"first": {"input": 450, "create": 0, "read": 30346}, "second": {"input": 450, "create": 0, "read": 30346}, "path": "hot |
| `cache_savings_measured` | 🟢 SUPPORTED (behavior verified) | 5.42s | cached call: input_tokens collapses; cache_read carries the prefix bulk | {"first": {"input": 14, "create": 0, "read": 13508}, "second": {"input": 14, "create": 0, "read": 13508}, "cache_volume" |
| `cache_ttl_1h` | 🟢 SUPPORTED (behavior verified) | 7.10s | ttl='1h' on cold cache: fresh write lands in ephemeral_1h_input_tokens (not 5m); second call reads it back | {"contract": "supported", "first": {"input": 14, "create_total": 39008, "read_total": 0, "create_5m": 0, "create_1h": 39 |
| `cache_ttl_mixed_5m_and_1h` | 🟢 SUPPORTED (behavior verified) | 7.07s | 5m + 1h in same request on cold cache: BOTH ephemeral_1h and ephemeral_5m populate on the fresh write; second call reads the sum | {"contract": "supported", "first_breakdown": {"ephemeral_1h_input_tokens": 34503, "ephemeral_5m_input_tokens": 31504}, " |
