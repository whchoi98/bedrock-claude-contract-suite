"""Single source of truth for model + region + provider settings.

To validate a future model or add a provider, only this file needs to change.
"""
import os

# Providers supported by the suite.
PROVIDERS = ("bedrock", "cpaws")
DEFAULT_PROVIDER = "bedrock"

# Model aliases mapped to per-provider concrete model IDs.
# An alias is the human-friendly identifier used in matrix rows.
MODEL_ALIASES = {
    "opus-4-7": {
        "bedrock": "global.anthropic.claude-opus-4-7",
        "cpaws":   "claude-opus-4-7",
    },
    "opus-4-6": {
        "bedrock": "global.anthropic.claude-opus-4-6-v1",
        "cpaws":   "claude-opus-4-6",
    },
    "sonnet-4-6": {
        "bedrock": "global.anthropic.claude-sonnet-4-6",
        "cpaws":   "claude-sonnet-4-6",
    },
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

# Features known to be Anthropic-direct only (skipped on Bedrock).
BEDROCK_UNSUPPORTED = {
    "files_api",
    "message_batches",
    "admin_api",
    "server_tool_web_search",
    "server_tool_code_execution",
    "server_tool_memory",
    "computer_use",
    "mcp_connector",
}
