# Bedrock × Anthropic Messages API verification

- **Started (UTC)**: 2026-05-20T06:39:16Z
- **Region**: `ap-northeast-2`
- **Model**: `claude-opus-4-7`
- **Result**: **3 / 3 passed**

## Result legend

| Icon | Meaning | Count |
| --- | --- | ---: |
| 🟢 | **Supported** — feature works on Bedrock; behavior verified | 3 |
| ⛔ | **Rejected (contract)** — feature is NOT supported on Bedrock; rejection verified | 0 |
| 🟡 | **Mixed** — partial support (e.g. header accepted, config rejected) | 0 |
| ❌ | **FAIL** — actual failure | 0 |

**Genuine feature support on this model+region**: 3 of 3 surfaces. 0 surfaces are confirmed unsupported. 0 are partially supported.

## Summary by category

| Category | Total | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client` | 1 | 1 | 0 | 0 | 0 |
| `multilingual` | 2 | 2 | 0 | 0 | 0 |

## Details

### `client` — 1 / 1

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `async_client` | 🟢 SUPPORTED (behavior verified) | 2.11s | Async client returns a valid Message on the same provider | {"reply": "async-ok", "stop_reason": "end_turn", "client_class": "AnthropicAWS"} |

### `multilingual` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `multilingual_japanese` | 🟢 SUPPORTED (behavior verified) | 2.50s | Japanese prompt yields a reply with Japanese script | {"reply": "\u3053\u3093\u306b\u3061\u306f\u3001\u304a\u5143\u6c17\u3067\u3059\u304b?"} |
| `multilingual_korean` | 🟢 SUPPORTED (behavior verified) | 1.92s | Korean prompt yields a reply containing Hangul characters | {"reply": "\uc548\ub155\ud558\uc138\uc694! \ub9cc\ub098\uc11c \ubc18\uac11\uc2b5\ub2c8\ub2e4. \ud83d\ude0a"} |
