# Bedrock × Anthropic Messages API verification

- **Started (UTC)**: 2026-05-12T23:00:13Z
- **Region**: `ap-northeast-2`
- **Model**: `claude-opus-4-7`
- **Result**: **52 / 57 passed**

## Result legend

| Icon | Meaning | Count |
| --- | --- | ---: |
| 🟢 | **Supported** — feature works on Bedrock; behavior verified | 46 |
| ⛔ | **Rejected (contract)** — feature is NOT supported on Bedrock; rejection verified | 6 |
| 🟡 | **Mixed** — partial support (e.g. header accepted, config rejected) | 0 |
| ❌ | **FAIL** — actual failure | 5 |

**Genuine feature support on this model+region**: 46 of 57 surfaces. 6 surfaces are confirmed unsupported. 0 are partially supported.

## Summary by category

| Category | Total | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail |
| --- | ---: | ---: | ---: | ---: | ---: |
| `caching` | 8 | 6 | 1 | 0 | 1 |
| `citations` | 2 | 2 | 0 | 0 | 0 |
| `client` | 1 | 0 | 0 | 0 | 1 |
| `context` | 2 | 2 | 0 | 0 | 0 |
| `documents` | 2 | 2 | 0 | 0 | 0 |
| `messages` | 11 | 9 | 2 | 0 | 0 |
| `multilingual` | 2 | 2 | 0 | 0 | 0 |
| `streaming` | 5 | 5 | 0 | 0 | 0 |
| `thinking` | 5 | 4 | 1 | 0 | 0 |
| `token_counting` | 1 | 1 | 0 | 0 | 0 |
| `tools` | 11 | 11 | 0 | 0 | 0 |
| `unsupported` | 5 | 0 | 2 | 0 | 3 |
| `vision` | 2 | 2 | 0 | 0 | 0 |

## Details

### `caching` — 7 / 8

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `extended_ttl_beta_header_rejected_on_bedrock` | ⛔ REJECTED (contract) | 2.41s | anthropic-beta: extended-cache-ttl-2025-04-11 is rejected on Bedrock | {"contract": "accepted", "note": "beta header now accepted \u2014 update README findings"} |
| `cache_multi_breakpoint` | 🟢 SUPPORTED (behavior verified) | 4.96s | system breakpoint AND user message breakpoint both register | {"first": {"input": 21, "create": 19507, "read": 0}, "second": {"input": 6, "create": 15, "read": 19507}, "path": "fresh |
| `cache_on_messages` | 🟢 SUPPORTED (behavior verified) | 4.95s | cache_control on a user content block triggers cache create/read | {"first": {"input": 25, "create": 10005, "read": 0}, "second": {"input": 6, "create": 19, "read": 10005}, "path": "fresh |
| `prompt_caching` | 🟢 SUPPORTED (behavior verified) | 5.65s | cache_control marks a system prefix; 2nd call shows cache_read_input_tokens | {"first_call_usage": {"input_tokens": 22, "output_tokens": 11, "cache_creation_input_tokens": 16520, "cache_read_input_t |
| `cache_on_tools` | 🟢 SUPPORTED (behavior verified) | 4.88s | cache_control attached to last tool definition triggers cache use | {"first": {"input": 450, "create": 30346, "read": 0}, "second": {"input": 6, "create": 444, "read": 30346}, "path": "fre |
| `cache_savings_measured` | 🟢 SUPPORTED (behavior verified) | 4.43s | cached call: input_tokens collapses; cache_read carries the prefix bulk | {"first": {"input": 14, "create": 13508, "read": 0}, "second": {"input": 6, "create": 8, "read": 13508}, "cache_volume": |
| `cache_ttl_1h` | ❌ FAIL | 4.30s | ttl='1h' on cold cache: fresh write lands in ephemeral_1h_input_tokens (not 5m); second call reads it back | second call did not read the 1h cache back. |
| `cache_ttl_mixed_5m_and_1h` | 🟢 SUPPORTED (behavior verified) | 5.74s | 5m + 1h in same request on cold cache: BOTH ephemeral_1h and ephemeral_5m populate on the fresh write; second call reads the sum | {"contract": "supported", "first": {"input": 19, "create_total": 21035, "read_total": 0, "create_5m": 9018, "create_1h": |

### `citations` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `citations_search_result_correct_source` | 🟢 SUPPORTED (behavior verified) | 1.95s | answer mentions Mei Tanaka AND citation points at the team source | {"answer_preview": "Mei Tanaka led Project Aurora as the lead engineer.", "cited_sources": ["https://example.com/aurora- |
| `citations` | 🟢 SUPPORTED (behavior verified) | 3.31s | document citations={enabled:true} produces citation entries on text blocks | {"cited_blocks": [{"text": "Mei Tanaka", "citation_count": 1}], "stop_reason": "end_turn"} |

### `client` — 0 / 1

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `async_client` | ❌ FAIL | 0.00s | AsyncAnthropicBedrock returns a valid Message | no bearer token |

### `context` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `context_1m_needle_in_haystack` | 🟢 SUPPORTED (behavior verified) | 6.98s | needle (unique fact) is recoverable from a >200K-token document | {"input_tokens": 233112, "output_tokens": 28, "needle_section": 4321, "stop_reason": "end_turn", "answer_preview": "PASS |
| `context_1m_beta` | 🟢 SUPPORTED (behavior verified) | 3.75s | anthropic-beta: context-1m-2025-08-07 accepted; long input round-trips | {"input_tokens": 17383, "stop_reason": "end_turn", "expected": "engineer-8", "preview": "engineer-8"} |

### `documents` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `pdf_document` | 🟢 SUPPORTED (behavior verified) | 1.69s | document content block (PDF base64) is parsed and answerable | {"reply": "BEDROCK_OPUS_PDF_OK", "stop_reason": "end_turn"} |
| `pdf_with_citations` | 🟢 SUPPORTED (behavior verified) | 2.15s | PDF base64 + citations:{enabled:true} returns at least one citation | {"cited_blocks": [{"text": "BEDROCK_OPUS_PDF_OK", "n": 1}], "stop_reason": "end_turn"} |

### `messages` — 11 / 11

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `assistant_prefill` | ⛔ REJECTED (contract) | 0.38s | prefill works (legacy) OR is cleanly rejected (Opus 4.7+ contract) | {"contract": "rejected", "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'mes |
| `context_editing_works` | 🟢 SUPPORTED (behavior verified) | 2.01s | context-management beta header + extra_body.context_management round-trips | {"tool_called": "echo", "stop_reason": "tool_use"} |
| `basic` | 🟢 SUPPORTED (behavior verified) | 2.83s | messages.create round-trip with one user turn | {"stop_reason": "end_turn", "input_tokens": 21, "output_tokens": 6, "text": "OK"} |
| `max_tokens_truncation` | 🟢 SUPPORTED (behavior verified) | 1.59s | very small max_tokens forces stop_reason=max_tokens | {"stop_reason": "max_tokens", "output_tokens": 4} |
| `metadata_user_id` | 🟢 SUPPORTED (behavior verified) | 2.05s | metadata={'user_id': ...} is accepted without 4xx | {"reply": "metadata-ok", "stop_reason": "end_turn"} |
| `multi_turn` | 🟢 SUPPORTED (behavior verified) | 1.71s | assistant uses prior-turn context to answer follow-up | {"reply": "Daisy"} |
| `sampling_params_deprecated` | ⛔ REJECTED (contract) | 1.92s | temperature/top_p/top_k: rejected with deprecation on Opus 4.7; accepted on Opus 4.6 / Sonnet 4.6 (legacy) | {"contract": "rejected_deprecated", "statuses": {"temperature": "deprecated", "top_p": "deprecated", "top_k": "deprecate |
| `service_tier` | 🟢 SUPPORTED (behavior verified) | 1.92s | service_tier='auto' is accepted, ignored, or cleanly rejected on Bedrock | {"reply": "tier-ok", "stop_reason": "end_turn"} |
| `stop_sequences` | 🟢 SUPPORTED (behavior verified) | 2.14s | stop_sequences trigger stop_reason=stop_sequence | {"stop_reason": "stop_sequence", "stop_sequence": "END", "preview": "A B C "} |
| `structured_outputs` | 🟢 SUPPORTED (behavior verified) | 2.90s | output_config.format=json_schema accepted on supported models; rejected on Opus 4.7 via Invoke API (Mantle required) | {"contract": "supported", "parsed": {"city": "Seoul"}, "stop_reason": "end_turn"} |
| `system_prompt` | 🟢 SUPPORTED (behavior verified) | 3.54s | system prompt steers reply style (string + blocks form) | {"upper_reply": "HELLO!", "lower_reply": "hello"} |

### `multilingual` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `multilingual_japanese` | 🟢 SUPPORTED (behavior verified) | 2.19s | Japanese prompt yields a reply with Japanese script | {"reply": "\u3053\u3093\u306b\u3061\u306f\u3001\u306f\u3058\u3081\u307e\u3057\u3066\u3002"} |
| `multilingual_korean` | 🟢 SUPPORTED (behavior verified) | 2.16s | Korean prompt yields a reply containing Hangul characters | {"reply": "\uc548\ub155\ud558\uc138\uc694! \ub9cc\ub098\uc11c \ubc18\uac11\uc2b5\ub2c8\ub2e4. \ud83d\ude0a"} |

### `streaming` — 5 / 5

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `event_schema` | 🟢 SUPPORTED (behavior verified) | 1.79s | stream emits message_start, content_block_start/stop, message_stop | {"types": ["content_block_delta", "content_block_start", "content_block_stop", "message_delta", "message_start", "messag |
| `fine_grained_tool_streaming_beta` | 🟢 SUPPORTED (behavior verified) | 2.82s | anthropic-beta: fine-grained-tool-streaming-2025-05-14 accepted; deltas observed | {"input_json_delta_seen": true, "fragments": 4, "tool_input": {"status": "ready", "level": 1}} |
| `streaming` | 🟢 SUPPORTED (behavior verified) | 2.23s | messages.stream() yields incremental text deltas | {"delta_count": 2, "event_kinds": ["ParsedContentBlockStopEvent", "ParsedMessageStopEvent", "RawContentBlockDeltaEvent", |
| `streaming_thinking` | 🟢 SUPPORTED (behavior verified) | 2.73s | stream with thinking yields thinking_delta or signature_delta events | {"delta_kinds": ["text_delta"], "block_kinds_seen": ["text"], "final_blocks": ["text"], "thinking_used": false} |
| `streaming_tool_use` | 🟢 SUPPORTED (behavior verified) | 2.79s | stream emits input_json_delta events that reconstruct tool input JSON | {"input_json_delta_seen": true, "fragments": 6, "reconstructed_preview": "{\"status\": \"ready\", \"level\": 1}", "tool_ |

### `thinking` — 5 / 5

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `extended_thinking` | 🟢 SUPPORTED (behavior verified) | 1.81s | thinking.type=adaptive + output_config.effort accepted; correct answer | {"blocks": ["text"], "thinking_block_present": false, "answer_preview": "30003", "stop_reason": "end_turn"} |
| `thinking_disabled` | 🟢 SUPPORTED (behavior verified) | 1.72s | thinking={type:disabled} returns text-only response | {"blocks": ["text"], "text": "4"} |
| `thinking_enabled_with_effort` | ⛔ REJECTED (contract) | 0.54s | thinking.type=enabled supported (legacy) or cleanly redirected (Opus 4.7+) | {"contract": "rejected_use_adaptive", "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request |
| `interleaved_thinking_between_tools` | 🟢 SUPPORTED (behavior verified) | 7.05s | thinking blocks appear after tool_result (interleaved with tool calls) | {"r1_blocks": ["thinking", "tool_use"], "r2_blocks": ["tool_use"], "coexisted_in_r1": true, "thinking_after_tool": false |
| `thinking_with_tools` | 🟢 SUPPORTED (behavior verified) | 6.91s | thinking + tool_use round trip preserves thinking block signature | {"first_blocks": ["tool_use"], "tool_input": {"a": 10000, "b": 7}, "final_preview": "10000 // 7 = **1428**\n\n### Explan |

### `token_counting` — 1 / 1

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `count_tokens` | 🟢 SUPPORTED (behavior verified) | 0.69s | messages.count_tokens via Anthropic SDK rejected on Bedrock with 'not supported in Bedrock yet'; AWS-native /model/{id}/count-tokens exists separately, see scripts/probe_token_counting.py | {"contract": "supported", "input_tokens": 17, "note": "Anthropic SDK count_tokens succeeded \u2014 Bedrock now exposes t |

### `tools` — 11 / 11

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `tool_use` | 🟢 SUPPORTED (behavior verified) | 4.62s | model selects a tool, then composes a final answer from tool_result | {"tool_called": "get_weather", "tool_input": {"city": "Seoul"}, "final": "The weather in Seoul is currently **sunny with |
| `builtin_bash_tool` | 🟢 SUPPORTED (behavior verified) | 2.79s | tools=[{type:bash_20250124}] is accepted; model uses it for shell-style requests | {"tool_called": "bash", "tool_input": {"command": "ls -la /tmp"}, "stop_reason": "tool_use"} |
| `builtin_memory_tool` | 🟢 SUPPORTED (behavior verified) | 3.11s | tools=[{type:memory_20250818}] — accepted on Opus 4.6/4.7, rejected on Sonnet 4.6 (not in expected-tags schema) | {"contract": "supported", "tool_called": "memory", "tool_input_keys": ["command", "path"], "stop_reason": "tool_use"} |
| `builtin_text_editor_tool` | 🟢 SUPPORTED (behavior verified) | 2.66s | tools=[{type:text_editor_20250728}] accepted; model emits the tool | {"tool_called": "str_replace_based_edit_tool", "stop_reason": "tool_use"} |
| `tool_choice` | 🟢 SUPPORTED (behavior verified) | 2.41s | tool_choice={type:tool, name:X} forces selection of X | {"tool_called": "shout", "stop_reason": "tool_use"} |
| `tool_choice_variants` | 🟢 SUPPORTED (behavior verified) | 5.48s | tool_choice supports any/none/auto with documented effects | {"any_called_tool": true, "none_avoided_tool": true, "auto_avoided_when_not_needed": true} |
| `disable_parallel_tool_use` | 🟢 SUPPORTED (behavior verified) | 2.88s | tool_choice with disable_parallel_tool_use=True yields one tool_use | {"tool_use_count": 1, "stop_reason": "tool_use"} |
| `parallel_tool_use` | 🟢 SUPPORTED (behavior verified) | 3.06s | model returns multiple tool_use blocks in one response | {"tool_use_count": 3, "cities": ["seoul", "sydney", "tokyo"], "stop_reason": "tool_use"} |
| `tool_result_image` | 🟢 SUPPORTED (behavior verified) | 4.49s | tool_result with image content is accepted | {"reply": "red.", "stop_reason": "end_turn"} |
| `strict_tool_use` | 🟢 SUPPORTED (behavior verified) | 2.46s | tools[].strict=True accepted on Opus 4.6 / Sonnet 4.6; rejected on Opus 4.7 (Invoke API) — Mantle required for that model | {"contract": "supported", "tool_input": {"status": "ok"}, "stop_reason": "tool_use"} |
| `token_efficient_tools_reduces_tokens` | 🟢 SUPPORTED (behavior verified) | 6.05s | WITH beta header, output_tokens <= WITHOUT (for same prompt + tool) | {"baseline": {"stop_reason": "tool_use", "input_tokens": 823, "output_tokens": 111, "tool_called": "describe_item", "pre |

### `unsupported` — 2 / 5

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `compaction_beta_header_rejected_on_bedrock` | ❌ FAIL | 0.59s | anthropic-beta: compaction-2025-09-17 rejected on Bedrock despite docs | {"contract": "rejected", "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'mes |
| `computer_use_tool_rejected_on_opus_4_7` | ⛔ REJECTED (contract) | 0.33s | tools=[{type:computer_20250124}] rejected on Bedrock Invoke API for Opus 4.7 / Opus 4.6 / Sonnet 4.6 | {"contract": "rejected", "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'mes |
| `bedrock_unsupported` | ❌ FAIL | 0.91s | Files / Batches / Models endpoints absent or refused on Bedrock | {"files": {"absent_or_error": true, "detail": "attribute_absent"}, "batches": {"absent_or_error": true, "detail": "attri |
| `server_tools_rejected` | ❌ FAIL | 6.93s | server tool types (web_search, web_fetch, code_execution) rejected on Bedrock | {"web_search": {"rejected": false, "detail": "accepted_unexpectedly"}, "web_fetch": {"rejected": false, "detail": "accep |
| `tool_search_tool_rejected_on_opus_4_7` | ⛔ REJECTED (contract) | 0.28s | tools=[{type:tool_search_tool_20250706}] rejected on Bedrock Invoke API for Opus 4.7 / Opus 4.6 / Sonnet 4.6 | {"contract": "rejected", "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'mes |

### `vision` — 2 / 2

| Test | Status | Time | Description | Notes |
| --- | --- | ---: | --- | --- |
| `vision` | 🟢 SUPPORTED (behavior verified) | 1.73s | model accepts an inline base64 PNG and describes it | {"reply": "red", "stop_reason": "end_turn"} |
| `vision_multi_image` | 🟢 SUPPORTED (behavior verified) | 2.50s | two inline images in one turn; model distinguishes them | {"reply": "red, green", "order_red_first": true} |
