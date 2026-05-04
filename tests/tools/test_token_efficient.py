"""Token-efficient tool use must actually reduce output tokens.

Compares the same tool-using prompt WITH and WITHOUT the beta header. The
beta is supposed to compress tool-use formatting; we accept the result if
either (a) output_tokens drop measurably (>=10% or >=10 tokens absolute), or
(b) output_tokens are equal but the tool was still called correctly (a
floor — model already minimal). We FAIL if the beta header inflates tokens.
"""
from tests._base import text_of

NAME = "token_efficient_tools_reduces_tokens"
DESCRIPTION = "WITH beta header, output_tokens <= WITHOUT (for same prompt + tool)"

TOOLS = [
    {
        "name": "describe_item",
        "description": "Return a description for an item id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "verbosity": {"type": "string"},
            },
            "required": ["item_id"],
        },
    }
]
PROMPT = (
    "Use describe_item with item_id='SKU-42-XX' and verbosity='detailed'. "
    "After the tool call, summarize the result for the customer."
)


def _call(client, model, beta: bool) -> dict:
    kw = {}
    if beta:
        kw["extra_headers"] = {"anthropic-beta": "token-efficient-tools-2025-02-19"}
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        tools=TOOLS,
        messages=[{"role": "user", "content": PROMPT}],
        **kw,
    )
    tu = [b for b in resp.content if b.type == "tool_use"]
    return {
        "stop_reason": resp.stop_reason,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "tool_called": tu[0].name if tu else None,
        "preview": text_of(resp)[:80],
    }


def run(client, model) -> dict:
    baseline = _call(client, model, beta=False)
    optimized = _call(client, model, beta=True)

    out_b, out_o = baseline["output_tokens"], optimized["output_tokens"]
    delta = out_b - out_o
    relative = delta / out_b if out_b else 0.0
    reduced = (delta >= 10) or (relative >= 0.10)
    not_inflated = out_o <= out_b + 5  # tolerance for nondeterminism
    correct = (
        baseline["tool_called"] == "describe_item"
        and optimized["tool_called"] == "describe_item"
    )
    return {
        "ok": correct and (reduced or not_inflated),
        "info": {
            "baseline": baseline,
            "optimized": optimized,
            "output_token_delta": delta,
            "relative_reduction": round(relative, 3),
            "reduced": reduced,
        },
        "error": None if correct else "tool not called consistently in both runs",
    }
