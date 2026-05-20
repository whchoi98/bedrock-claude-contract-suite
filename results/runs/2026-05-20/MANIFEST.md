# Matrix run snapshot — 2026-05-20

## Git

- SHA: `66b4f2c`
- State: dirty (uncommitted changes)

## Command

```bash
python3 run_all.py --providers bedrock cpaws --all-models
```

## Environment (secrets redacted)

- `AWS_BEARER_TOKEN_BEDROCK` = `ABSKQm…<redacted, len=132>`
- `AWS_REGION` = `ap-northeast-2`
- `BEDROCK_MODEL_ID` = `global.anthropic.claude-opus-4-7`
- `ANTHROPIC_AWS_API_KEY` = `AEAAQW…<redacted, len=132>`
- `ANTHROPIC_AWS_WORKSPACE_ID` = `wrkspc…<redacted, len=31>`
- `CPAWS_REGION` = `us-east-2`

## Concrete model IDs used

| Provider | Alias | Model ID |
| --- | --- | --- |
| `bedrock` | `opus-4-7` | `global.anthropic.claude-opus-4-7` |
| `bedrock` | `sonnet-4-6` | `global.anthropic.claude-sonnet-4-6` |
| `cpaws` | `opus-4-7` | `claude-opus-4-7` |
| `cpaws` | `sonnet-4-6` | `claude-sonnet-4-6` |

## Per-cell totals

| Provider | Alias | Passed | Total |
| --- | --- | ---: | ---: |
| `bedrock` | `opus-4-7` | 57 | 57 |
| `bedrock` | `sonnet-4-6` | 57 | 57 |
| `cpaws` | `opus-4-7` | 53 | 57 |
| `cpaws` | `sonnet-4-6` | 49 | 57 |

## Files in this snapshot

- `matrix.{json,md}` — full 2-provider × 2-model matrix (verbatim run output)
- `bedrock.md` / `cpaws.md` — per-provider sub-matrices for at-a-glance comparison
- `tests-snapshot/` — `probes/` package at run time (the canonical, reusable form of every probe). Importable as a Python module.
- `MANIFEST.md` — this file

## Notes on failures (read before interpreting ❌)

### Tier 1 rate-limit blocked (not a contract issue)

These probes' input size alone exceeds the workspace's 30k ITPM; SDK retries do not help.

- `cpaws/sonnet-4-6: context/context_1m_beta`
- `cpaws/sonnet-4-6: documents/pdf_document`
- `cpaws/sonnet-4-6: documents/pdf_with_citations`

### Contract divergence captured (probe expects Bedrock shape)

These probes' pass-condition is shaped around Bedrock's rejection. The opposing provider (CPaws) accepts the surface — ❌ here documents *where the providers diverge*, not where the probe is broken. Compare with the corresponding row in `cpaws_findings.md §A`.

- `cpaws/opus-4-7: unsupported/compaction_beta_header_rejected_on_bedrock`
- `cpaws/opus-4-7: unsupported/bedrock_unsupported`
- `cpaws/opus-4-7: unsupported/server_tools_rejected`
- `cpaws/sonnet-4-6: unsupported/compaction_beta_header_rejected_on_bedrock`
- `cpaws/sonnet-4-6: unsupported/bedrock_unsupported`
- `cpaws/sonnet-4-6: unsupported/server_tools_rejected`

### Other failures (investigate)

Failures not classified above. These are either real contract changes, transient errors, or probe assertions that need refinement.

- `cpaws/opus-4-7: caching/cache_ttl_1h`
- `cpaws/sonnet-4-6: caching/cache_ttl_1h`
- `cpaws/sonnet-4-6: streaming/streaming`
