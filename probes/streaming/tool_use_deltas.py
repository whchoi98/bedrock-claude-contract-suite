"""During streaming, tool_use input arrives as input_json_delta events."""
NAME = "streaming_tool_use"
DESCRIPTION = "stream emits input_json_delta events that reconstruct tool input JSON"

TOOLS = [
    {
        "name": "set_status",
        "description": "Set a status.",
        "input_schema": {
            "type": "object",
            "properties": {"status": {"type": "string"}, "level": {"type": "integer"}},
            "required": ["status", "level"],
        },
    }
]


def run(client, model) -> dict:
    json_fragments: list[str] = []
    saw_input_json_delta = False
    with client.messages.stream(
        model=model,
        max_tokens=256,
        tools=TOOLS,
        messages=[{"role": "user", "content": "Use set_status with status='ready', level=1."}],
    ) as stream:
        for event in stream:
            delta = getattr(event, "delta", None)
            if delta is not None and getattr(delta, "type", None) == "input_json_delta":
                saw_input_json_delta = True
                json_fragments.append(delta.partial_json or "")
        final = stream.get_final_message()

    tool_blocks = [b for b in final.content if b.type == "tool_use"]
    reconstructed = "".join(json_fragments)
    return {
        "ok": saw_input_json_delta and bool(tool_blocks)
              and tool_blocks[0].input.get("status") == "ready",
        "info": {
            "input_json_delta_seen": saw_input_json_delta,
            "fragments": len(json_fragments),
            "reconstructed_preview": reconstructed[:80],
            "tool_input": dict(tool_blocks[0].input) if tool_blocks else None,
        },
    }
