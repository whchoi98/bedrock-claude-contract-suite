"""Single source of truth for model + region settings.

To validate a future model, only this file needs to change.
"""
import os

# Bedrock inference-profile-prefixed model ID (default for single-model runs).
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-opus-4-7")

# All models to test when running in multi-model mode (--all-models flag).
ALL_MODELS = [
    "global.anthropic.claude-opus-4-7",
    "global.anthropic.claude-opus-4-6-v1",
    "global.anthropic.claude-sonnet-4-6",
]

# Region used by the SDK to construct the Bedrock endpoint.
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")

# Default token budget for short probes.
DEFAULT_MAX_TOKENS = 256

# Beta headers required for specific features.
BETA_1M_CONTEXT = "context-1m-2025-08-07"
BETA_PDF_DOCUMENTS = "pdfs-2024-09-25"          # generally GA but harmless
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
