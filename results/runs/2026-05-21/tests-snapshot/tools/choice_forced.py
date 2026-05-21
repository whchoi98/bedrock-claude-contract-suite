"""tool_choice forces a specific tool selection."""
NAME = "tool_choice"
DESCRIPTION = "tool_choice={type:tool, name:X} forces selection of X"

TOOLS = [
    {
        "name": "echo",
        "description": "Echo a phrase.",
        "input_schema": {
            "type": "object",
            "properties": {"phrase": {"type": "string"}},
            "required": ["phrase"],
        },
    },
    {
        "name": "shout",
        "description": "Shout a phrase in uppercase.",
        "input_schema": {
            "type": "object",
            "properties": {"phrase": {"type": "string"}},
            "required": ["phrase"],
        },
    },
]


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=128,
        tools=TOOLS,
        tool_choice={"type": "tool", "name": "shout"},
        messages=[{"role": "user", "content": "Process: hello there"}],
    )
    tool_blocks = [b for b in resp.content if b.type == "tool_use"]
    return {
        "ok": bool(tool_blocks) and tool_blocks[0].name == "shout",
        "info": {
            "tool_called": tool_blocks[0].name if tool_blocks else None,
            "stop_reason": resp.stop_reason,
        },
    }
