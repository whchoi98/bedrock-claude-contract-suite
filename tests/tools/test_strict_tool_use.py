"""Strict tool use (`tools[].strict=true`) — model-divergent on Bedrock.

Opus 4.6 / Sonnet 4.6 (Invoke API) → accepted; the model is forced to
produce schema-conformant tool arguments.
Opus 4.7 (Invoke API) → rejected with
`tools.0.custom.strict: Extra inputs are not permitted` (Mantle is the
docs-recommended fallback but is out of scope here).
"""
from anthropic import BadRequestError

NAME = "strict_tool_use"
DESCRIPTION = (
    "tools[].strict=True accepted on Opus 4.6 / Sonnet 4.6; rejected on "
    "Opus 4.7 (Invoke API) — Mantle required for that model"
)


def run(client, model) -> dict:
    tool = {
        "name": "set_status",
        "description": "Record the status",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
            "additionalProperties": False,
        },
    }
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=64,
            tools=[tool],
            tool_choice={"type": "tool", "name": "set_status"},
            messages=[
                {"role": "user", "content": "Use set_status with status='ok'."}
            ],
        )
    except BadRequestError as e:
        msg = (e.message or "")[:280]
        rejected = "strict" in msg.lower() and "extra inputs" in msg.lower()
        return {
            "ok": rejected,
            "info": {
                "contract": "rejected_on_invoke_for_this_model",
                "message": msg,
                "note": (
                    "Mantle (`bedrock-mantle.{region}.api.aws`) is the "
                    "docs-recommended fallback for Opus 4.7 but is out of "
                    "scope for this suite — see results/docs_vs_reality.md."
                ),
            },
        }

    tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
    if not tool_uses:
        return {
            "ok": False,
            "info": {
                "contract": "supported_but_no_tool_use",
                "stop_reason": resp.stop_reason,
            },
            "error": "API accepted strict=True but produced no tool_use block.",
        }
    inp = tool_uses[0].input or {}
    schema_conformant = isinstance(inp, dict) and "status" in inp and isinstance(inp["status"], str)
    return {
        "ok": schema_conformant,
        "info": {
            "contract": "supported",
            "tool_input": inp,
            "stop_reason": resp.stop_reason,
        },
        "error": None if schema_conformant else (
            f"strict=True accepted but tool_input did not match schema: {inp!r}"
        ),
    }
