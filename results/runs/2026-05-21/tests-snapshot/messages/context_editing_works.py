"""Context editing on Bedrock: works when beta header + config are both supplied.

A previous test found the config alone is rejected. With both the
`context-management-2025-06-27` beta header AND `extra_body.context_management`,
the request is accepted and the model proceeds with its tool call.
"""
NAME = "context_editing_works"
DESCRIPTION = "context-management beta header + extra_body.context_management round-trips"

TOOLS = [
    {
        "name": "echo",
        "description": "echo",
        "input_schema": {
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
    }
]


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=128,
        tools=TOOLS,
        extra_headers={"anthropic-beta": "context-management-2025-06-27"},
        extra_body={
            "context_management": {
                "edits": [{"type": "clear_tool_uses_20250919"}]
            }
        },
        messages=[{"role": "user", "content": "Use echo with x='ping'."}],
    )
    tu = [b for b in resp.content if b.type == "tool_use"]
    return {
        "ok": bool(tu) and resp.stop_reason in ("tool_use", "end_turn"),
        "info": {
            "tool_called": tu[0].name if tu else None,
            "stop_reason": resp.stop_reason,
        },
    }
