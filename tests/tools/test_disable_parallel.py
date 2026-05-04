"""disable_parallel_tool_use forces sequential tool calls (one tool_use block)."""
NAME = "disable_parallel_tool_use"
DESCRIPTION = "tool_choice with disable_parallel_tool_use=True yields one tool_use"

TOOLS = [
    {
        "name": "lookup",
        "description": "Look up a value.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    }
]


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        tools=TOOLS,
        tool_choice={"type": "auto", "disable_parallel_tool_use": True},
        messages=[
            {
                "role": "user",
                "content": "Look up 'a', 'b', and 'c'. Use the tool.",
            }
        ],
    )
    tu = [b for b in resp.content if b.type == "tool_use"]
    return {
        "ok": len(tu) <= 1 and (len(tu) == 1 or resp.stop_reason == "end_turn"),
        "info": {"tool_use_count": len(tu), "stop_reason": resp.stop_reason},
    }
