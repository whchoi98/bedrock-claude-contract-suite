"""Backwards-compat shim — implementations live in probes._base.

Tests still import from `tests._base` via the runner's auto-discovery
path. New code should import directly from `probes._base`.
"""
from probes._base import (  # noqa: F401
    Result,
    execute,
    is_unsupported_tool_rejection,
    text_of,
    usage_breakdown,
)
