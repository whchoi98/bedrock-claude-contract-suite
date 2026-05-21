# `bedrock` — single-provider matrix

- **Date**: 2026-05-21
- **Models**: ['opus-4-7', 'sonnet-4-6']

## Totals

| Model | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `opus-4-7` | 45 | 12 | 0 | 0 | 57 |
| `sonnet-4-6` | 48 | 9 | 0 | 0 | 57 |

## Test × Model matrix

### `caching`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `cache_multi_breakpoint` | 🟢 | 🟢 |
| `cache_on_messages` | 🟢 | 🟢 |
| `cache_on_tools` | 🟢 | 🟢 |
| `cache_savings_measured` | 🟢 | 🟢 |
| `cache_ttl_1h` | 🟢 | 🟢 |
| `cache_ttl_mixed_5m_and_1h` | 🟢 | 🟢 |
| `extended_ttl_beta_header_rejected_on_bedrock` | ⛔ | ⛔ |
| `prompt_caching` | 🟢 | 🟢 |

### `citations`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `citations` | 🟢 | 🟢 |
| `citations_search_result_correct_source` | 🟢 | 🟢 |

### `client`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `async_client` | 🟢 | 🟢 |

### `context`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `context_1m_beta` | 🟢 | 🟢 |
| `context_1m_needle_in_haystack` | 🟢 | 🟢 |

### `documents`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `pdf_document` | 🟢 | 🟢 |
| `pdf_with_citations` | 🟢 | 🟢 |

### `messages`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `assistant_prefill` | ⛔ | ⛔ |
| `basic` | 🟢 | 🟢 |
| `context_editing_works` | 🟢 | 🟢 |
| `max_tokens_truncation` | 🟢 | 🟢 |
| `metadata_user_id` | 🟢 | 🟢 |
| `multi_turn` | 🟢 | 🟢 |
| `sampling_params_deprecated` | ⛔ | ⛔ |
| `service_tier` | 🟢 | 🟢 |
| `stop_sequences` | 🟢 | 🟢 |
| `structured_outputs` | ⛔ | 🟢 |
| `system_prompt` | 🟢 | 🟢 |

### `multilingual`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `multilingual_japanese` | 🟢 | 🟢 |
| `multilingual_korean` | 🟢 | 🟢 |

### `streaming`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `event_schema` | 🟢 | 🟢 |
| `fine_grained_tool_streaming_beta` | 🟢 | 🟢 |
| `streaming` | 🟢 | 🟢 |
| `streaming_thinking` | 🟢 | 🟢 |
| `streaming_tool_use` | 🟢 | 🟢 |

### `thinking`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `extended_thinking` | 🟢 | 🟢 |
| `interleaved_thinking_between_tools` | 🟢 | 🟢 |
| `thinking_disabled` | 🟢 | 🟢 |
| `thinking_enabled_with_effort` | ⛔ | 🟢 |
| `thinking_with_tools` | 🟢 | 🟢 |

### `token_counting`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `count_tokens` | ⛔ | ⛔ |

### `tools`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `builtin_bash_tool` | 🟢 | 🟢 |
| `builtin_memory_tool` | 🟢 | 🟢 |
| `builtin_text_editor_tool` | 🟢 | 🟢 |
| `disable_parallel_tool_use` | 🟢 | 🟢 |
| `parallel_tool_use` | 🟢 | 🟢 |
| `strict_tool_use` | ⛔ | 🟢 |
| `token_efficient_tools_reduces_tokens` | 🟢 | 🟢 |
| `tool_choice` | 🟢 | 🟢 |
| `tool_choice_variants` | 🟢 | 🟢 |
| `tool_result_image` | 🟢 | 🟢 |
| `tool_use` | 🟢 | 🟢 |

### `unsupported`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `bedrock_unsupported` | ⛔ | ⛔ |
| `compaction_beta_header_rejected_on_bedrock` | ⛔ | ⛔ |
| `computer_use_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |
| `server_tools_rejected` | ⛔ | ⛔ |
| `tool_search_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |

### `vision`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `vision` | 🟢 | 🟢 |
| `vision_multi_image` | 🟢 | 🟢 |
