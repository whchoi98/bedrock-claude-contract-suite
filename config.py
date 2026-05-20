"""Single source of truth for model + region + provider settings.

To validate a future model or add a provider, only this file needs to change.
"""
import os

# Providers supported by the suite.
PROVIDERS = ("bedrock", "cpaws")
DEFAULT_PROVIDER = "bedrock"

# Model aliases mapped to per-provider concrete model IDs.
# An alias is the human-friendly identifier used in matrix rows.
#
# Model ID formats (verified empirically 2026-05-20):
#  - bedrock: `global.anthropic.claude-...` (cross-region inference prefix
#    `global.` works in any region; haiku-4-5 needs the dated `-v1:0` suffix)
#  - cpaws:   bare `claude-...` (NOT `anthropic:claude-...` — that prefix
#    was tested and returns 404 not_found_error. Bare IDs match what
#    `models.list()` returns and match what `messages.create()` accepts.)
MODEL_ALIASES = {
    "opus-4-7": {
        "bedrock": "global.anthropic.claude-opus-4-7",
        "cpaws":   "claude-opus-4-7",
    },
    "sonnet-4-6": {
        "bedrock": "global.anthropic.claude-sonnet-4-6",
        "cpaws":   "claude-sonnet-4-6",
    },
    # haiku-4-5 was tested on 2026-05-20 but excluded from the matrix:
    # CPaws Tier 1 sustained 529 Overloaded for haiku, making the contract
    # signal indistinguishable from infrastructure noise. Bedrock haiku
    # baseline retained in dated snapshots (results/runs/2026-05-20/).
    # To re-enable, add the alias back here and re-run --all-models.
    #   bedrock id: "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    #   cpaws id:   "claude-haiku-4-5-20251001"
}

# All model aliases iterated in --all-models mode.
ALL_MODELS = list(MODEL_ALIASES.keys())

# Default single-model alias. BEDROCK_MODEL_ID env var still accepted for
# backward compatibility: if set, it is the concrete Bedrock model ID and
# overrides MODEL_ID resolution for single-model bedrock runs.
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-opus-4-7")

# Region used by both providers (CPaws also honors CPAWS_REGION).
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")

# Default token budget for short probes.
DEFAULT_MAX_TOKENS = 256

# Beta headers required for specific features.
BETA_1M_CONTEXT = "context-1m-2025-08-07"
BETA_PDF_DOCUMENTS = "pdfs-2024-09-25"
BETA_INTERLEAVED_THINKING = "interleaved-thinking-2025-05-14"

# Features known to be Anthropic-direct only (rejected on Bedrock, accepted on CPaws).
# Empirically verified 2026-05-12 against `claude-opus-4-7` on both providers.
# See `results/cpaws_findings.md` for the per-feature cross-provider matrix.
BEDROCK_UNSUPPORTED = {
    "files_api",
    "message_batches",
    "admin_api",
    "server_tool_web_search",
    "server_tool_web_fetch",
    "server_tool_code_execution",
    "server_tool_memory",
    "computer_use",                  # Note: also rejected on CPaws — Anthropic-level gating
    "mcp_connector",
}
