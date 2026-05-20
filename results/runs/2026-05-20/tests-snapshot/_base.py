"""Tiny test harness primitives.

Each test module exposes:
    NAME: str          # short, stable identifier
    DESCRIPTION: str   # what's being verified
    def run(client, model) -> dict
        Must return {"ok": bool, "info": dict, "error": str | None}.
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Result:
    name: str
    description: str
    ok: bool
    info: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    elapsed_s: float = 0.0


def execute(
    name: str,
    description: str,
    fn: Callable[[], dict[str, Any]],
) -> Result:
    """Run a test function defensively and capture timing + errors."""
    start = time.perf_counter()
    try:
        out = fn()
        ok = bool(out.get("ok", False))
        return Result(
            name=name,
            description=description,
            ok=ok,
            info=out.get("info", {}),
            error=out.get("error"),
            elapsed_s=time.perf_counter() - start,
        )
    except Exception as e:  # noqa: BLE001 — we surface every failure mode
        return Result(
            name=name,
            description=description,
            ok=False,
            info={},
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}",
            elapsed_s=time.perf_counter() - start,
        )


def text_of(message) -> str:
    """Concatenate text blocks from a Messages API response."""
    return "".join(b.text for b in message.content if getattr(b, "type", None) == "text")


def usage_breakdown(usage) -> dict[str, Any]:
    """Flatten cache_creation usage into the shape every cache test needs."""
    cc = getattr(usage, "cache_creation", None)
    bd = cc.model_dump() if cc is not None else {}
    return {
        "input": usage.input_tokens,
        "create_total": getattr(usage, "cache_creation_input_tokens", 0),
        "read_total": getattr(usage, "cache_read_input_tokens", 0),
        "create_5m": bd.get("ephemeral_5m_input_tokens", 0),
        "create_1h": bd.get("ephemeral_1h_input_tokens", 0),
    }


def is_unsupported_tool_rejection(message: str, tool_type: str | None = None) -> bool:
    """True if a Bedrock 400 message indicates the tool type was rejected.

    Bedrock returns one of two equivalent forms:
      - "<...> not supported on this model"
      - "Input tag '<tool_type>' found using 'type' does not match any of
         the expected tags: ..."  (current SDK schema-validation form)
    """
    m = message.lower()
    if "not supported" in m:
        return True
    if "input tag" in m and "expected tags" in m:
        return True
    if tool_type and tool_type.lower() in m and "does not match" in m:
        return True
    return False
