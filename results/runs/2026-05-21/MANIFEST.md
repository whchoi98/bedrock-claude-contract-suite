# Matrix run snapshot — 2026-05-21

## Git

- SHA: `7475dba`
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
| `cpaws` | `sonnet-4-6` | 46 | 57 |

## Files in this snapshot

- `matrix.{json,md}` — full 2-provider × 2-model matrix (verbatim run output)
- `bedrock.md` / `cpaws.md` — per-provider sub-matrices for at-a-glance comparison
- `tests-snapshot/` — `probes/` package at run time (the canonical, reusable form of every probe). Importable as a Python module.
- `MANIFEST.md` — this file

## Notes on failures (read before interpreting ❌)

### Tier 1 rate-limit blocked (not a contract issue)

CPaws Tier 1 = **30,000 input tokens / rolling minute window** per
workspace. This rerun (2026-05-21) revealed two distinct failure modes:

**(a) Single-call payload alone exceeds the per-minute budget** —
SDK retries cannot help because the request itself overflows the
window. These probes are *structurally* incompatible with Tier 1:
- `cpaws/sonnet-4-6: documents/pdf_document` (~32k input tokens)
- `cpaws/sonnet-4-6: documents/pdf_with_citations` (~32k input tokens)
- `cpaws/sonnet-4-6: context/context_1m_beta` (>200k input tokens)

(Preserved from prior matrix via `rerun_cells.py --skip-tests` —
re-running these wastes API quota on guaranteed 429s.)

**(b) Cumulative TPM exhaustion within a 60-second window** —
These probes have small input but were rate-limited because earlier
probes in the same minute had exhausted the workspace budget. Observed
on this rerun even with 8-second inter-probe pacing:
- `cpaws/sonnet-4-6: messages/basic` (~50 tokens — NEW vs. 2026-05-20)
- `cpaws/sonnet-4-6: messages/max_tokens_truncation` (~30 tokens — NEW)
- `cpaws/sonnet-4-6: messages/context_editing_works` (~50 tokens — NEW)

**Implication of mode (b)**: Tier 1 is **non-deterministic at the
probe level** — the same small probe may pass or fail depending on
what ran in the preceding 60 seconds. Mitigations: longer pacing
(15-30s), batch into multiple minute windows, or upgrade to Tier 2+.
The 2026-05-20 baseline (49/57) and 2026-05-21 rerun (46/57) differ
*only* on these 3 cumulative-TPM probes — neither result is "wrong",
both reflect Tier 1's natural variance.

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
