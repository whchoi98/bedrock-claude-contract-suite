# Bedrock × Anthropic API — provider × model matrix

- **Region**: `ap-northeast-2`
- **Started (UTC)**: 2026-05-20T06:40:14Z
- **Providers**: ['bedrock', 'cpaws']
- **Total runs**: 4

## Per-provider × per-model totals

| Provider | Model | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `bedrock` | `opus-4-7` | 45 | 12 | 0 | 0 | 57 |
| `bedrock` | `sonnet-4-6` | 48 | 9 | 0 | 0 | 57 |
| `cpaws` | `opus-4-7` | 47 | 6 | 0 | 4 | 57 |
| `cpaws` | `sonnet-4-6` | 41 | 5 | 0 | 11 | 57 |

## Test × Model matrix

### `bedrock`

#### `caching`

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

#### `citations`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `citations` | 🟢 | 🟢 |
| `citations_search_result_correct_source` | 🟢 | 🟢 |

#### `client`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `async_client` | 🟢 | 🟢 |

#### `context`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `context_1m_beta` | 🟢 | 🟢 |
| `context_1m_needle_in_haystack` | 🟢 | 🟢 |

#### `documents`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `pdf_document` | 🟢 | 🟢 |
| `pdf_with_citations` | 🟢 | 🟢 |

#### `messages`

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

#### `multilingual`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `multilingual_japanese` | 🟢 | 🟢 |
| `multilingual_korean` | 🟢 | 🟢 |

#### `streaming`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `event_schema` | 🟢 | 🟢 |
| `fine_grained_tool_streaming_beta` | 🟢 | 🟢 |
| `streaming` | 🟢 | 🟢 |
| `streaming_thinking` | 🟢 | 🟢 |
| `streaming_tool_use` | 🟢 | 🟢 |

#### `thinking`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `extended_thinking` | 🟢 | 🟢 |
| `interleaved_thinking_between_tools` | 🟢 | 🟢 |
| `thinking_disabled` | 🟢 | 🟢 |
| `thinking_enabled_with_effort` | ⛔ | 🟢 |
| `thinking_with_tools` | 🟢 | 🟢 |

#### `token_counting`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `count_tokens` | ⛔ | ⛔ |

#### `tools`

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

#### `unsupported`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `bedrock_unsupported` | ⛔ | ⛔ |
| `compaction_beta_header_rejected_on_bedrock` | ⛔ | ⛔ |
| `computer_use_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |
| `server_tools_rejected` | ⛔ | ⛔ |
| `tool_search_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |

#### `vision`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `vision` | 🟢 | 🟢 |
| `vision_multi_image` | 🟢 | 🟢 |

### `cpaws`

#### `caching`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `cache_multi_breakpoint` | 🟢 | 🟢 |
| `cache_on_messages` | 🟢 | 🟢 |
| `cache_on_tools` | 🟢 | 🟢 |
| `cache_savings_measured` | 🟢 | 🟢 |
| `cache_ttl_1h` | ❌ | ❌ |
| `cache_ttl_mixed_5m_and_1h` | 🟢 | 🟢 |
| `extended_ttl_beta_header_rejected_on_bedrock` | ⛔ | ⛔ |
| `prompt_caching` | 🟢 | 🟢 |

#### `citations`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `citations` | 🟢 | 🟢 |
| `citations_search_result_correct_source` | 🟢 | 🟢 |

#### `client`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `async_client` | 🟢 | 🟢 |

#### `context`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `context_1m_beta` | 🟢 | ❌ |
| `context_1m_needle_in_haystack` | 🟢 | 🟢 |

#### `documents`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `pdf_document` | 🟢 | ❌ |
| `pdf_with_citations` | 🟢 | ❌ |

#### `messages`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `assistant_prefill` | ⛔ | ⛔ |
| `basic` | 🟢 | ❌ |
| `context_editing_works` | 🟢 | ❌ |
| `max_tokens_truncation` | 🟢 | ❌ |
| `metadata_user_id` | 🟢 | 🟢 |
| `multi_turn` | 🟢 | 🟢 |
| `sampling_params_deprecated` | ⛔ | ⛔ |
| `service_tier` | 🟢 | 🟢 |
| `stop_sequences` | 🟢 | 🟢 |
| `structured_outputs` | 🟢 | 🟢 |
| `system_prompt` | 🟢 | 🟢 |

#### `multilingual`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `multilingual_japanese` | 🟢 | 🟢 |
| `multilingual_korean` | 🟢 | 🟢 |

#### `streaming`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `event_schema` | 🟢 | 🟢 |
| `fine_grained_tool_streaming_beta` | 🟢 | 🟢 |
| `streaming` | 🟢 | ❌ |
| `streaming_thinking` | 🟢 | 🟢 |
| `streaming_tool_use` | 🟢 | 🟢 |

#### `thinking`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `extended_thinking` | 🟢 | 🟢 |
| `interleaved_thinking_between_tools` | 🟢 | 🟢 |
| `thinking_disabled` | 🟢 | 🟢 |
| `thinking_enabled_with_effort` | ⛔ | 🟢 |
| `thinking_with_tools` | 🟢 | 🟢 |

#### `token_counting`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `count_tokens` | 🟢 | 🟢 |

#### `tools`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `builtin_bash_tool` | 🟢 | 🟢 |
| `builtin_memory_tool` | 🟢 | 🟢 |
| `builtin_text_editor_tool` | 🟢 | 🟢 |
| `disable_parallel_tool_use` | 🟢 | 🟢 |
| `parallel_tool_use` | 🟢 | 🟢 |
| `strict_tool_use` | 🟢 | 🟢 |
| `token_efficient_tools_reduces_tokens` | 🟢 | 🟢 |
| `tool_choice` | 🟢 | 🟢 |
| `tool_choice_variants` | 🟢 | 🟢 |
| `tool_result_image` | 🟢 | 🟢 |
| `tool_use` | 🟢 | 🟢 |

#### `unsupported`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `bedrock_unsupported` | ❌ | ❌ |
| `compaction_beta_header_rejected_on_bedrock` | ❌ | ❌ |
| `computer_use_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |
| `server_tools_rejected` | ❌ | ❌ |
| `tool_search_tool_rejected_on_opus_4_7` | ⛔ | ⛔ |

#### `vision`

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `vision` | 🟢 | 🟢 |
| `vision_multi_image` | 🟢 | 🟢 |

## Cross-provider differences

19 (test, alias) pair(s) where providers disagree:

| Test | Alias | `bedrock` | `cpaws` |
| --- | --- | :---: | :---: |
| `basic` | `sonnet-4-6` | 🟢 | ❌ |
| `bedrock_unsupported` | `opus-4-7` | ⛔ | ❌ |
| `bedrock_unsupported` | `sonnet-4-6` | ⛔ | ❌ |
| `cache_ttl_1h` | `opus-4-7` | 🟢 | ❌ |
| `cache_ttl_1h` | `sonnet-4-6` | 🟢 | ❌ |
| `compaction_beta_header_rejected_on_bedrock` | `opus-4-7` | ⛔ | ❌ |
| `compaction_beta_header_rejected_on_bedrock` | `sonnet-4-6` | ⛔ | ❌ |
| `context_1m_beta` | `sonnet-4-6` | 🟢 | ❌ |
| `context_editing_works` | `sonnet-4-6` | 🟢 | ❌ |
| `count_tokens` | `opus-4-7` | ⛔ | 🟢 |
| `count_tokens` | `sonnet-4-6` | ⛔ | 🟢 |
| `max_tokens_truncation` | `sonnet-4-6` | 🟢 | ❌ |
| `pdf_document` | `sonnet-4-6` | 🟢 | ❌ |
| `pdf_with_citations` | `sonnet-4-6` | 🟢 | ❌ |
| `server_tools_rejected` | `opus-4-7` | ⛔ | ❌ |
| `server_tools_rejected` | `sonnet-4-6` | ⛔ | ❌ |
| `streaming` | `sonnet-4-6` | 🟢 | ❌ |
| `strict_tool_use` | `opus-4-7` | ⛔ | 🟢 |
| `structured_outputs` | `opus-4-7` | ⛔ | 🟢 |

## Inter-model differences (within each provider)

### `bedrock`

3 test(s) where models disagree:

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `strict_tool_use` | ⛔ rejected | 🟢 behavioral |
| `structured_outputs` | ⛔ rejected | 🟢 behavioral |
| `thinking_enabled_with_effort` | ⛔ rejected | 🟢 behavioral |

### `cpaws`

8 test(s) where models disagree:

| Test | `opus-4-7` | `sonnet-4-6` |
| --- | :---: | :---: |
| `basic` | 🟢 behavioral | ❌ fail |
| `context_1m_beta` | 🟢 behavioral | ❌ fail |
| `context_editing_works` | 🟢 behavioral | ❌ fail |
| `max_tokens_truncation` | 🟢 behavioral | ❌ fail |
| `pdf_document` | 🟢 behavioral | ❌ fail |
| `pdf_with_citations` | 🟢 behavioral | ❌ fail |
| `streaming` | 🟢 behavioral | ❌ fail |
| `thinking_enabled_with_effort` | ⛔ rejected | 🟢 behavioral |
