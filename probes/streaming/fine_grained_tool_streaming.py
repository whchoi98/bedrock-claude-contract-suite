"""Fine-grained tool streaming beta: tool input arrives as partial JSON deltas during stream."""
NAME = "fine_grained_tool_streaming_beta"
DESCRIPTION = "anthropic-beta: fine-grained-tool-streaming-2025-05-14 accepted; deltas observed"

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
    saw_input_json_delta = False
    fragments = 0
    with client.messages.stream(
        model=model,
        max_tokens=256,
        tools=TOOLS,
        messages=[{"role": "user", "content": "Use set_status with status='ready', level=1."}],
        extra_headers={"anthropic-beta": "fine-grained-tool-streaming-2025-05-14"},
    ) as stream:
        for event in stream:
            d = getattr(event, "delta", None)
            if d is not None and getattr(d, "type", None) == "input_json_delta":
                saw_input_json_delta = True
                fragments += 1
        final = stream.get_final_message()

    tool_blocks = [b for b in final.content if b.type == "tool_use"]
    return {
        "ok": saw_input_json_delta and bool(tool_blocks)
              and tool_blocks[0].input.get("status") == "ready",
        "info": {
            "input_json_delta_seen": saw_input_json_delta,
            "fragments": fragments,
            "tool_input": dict(tool_blocks[0].input) if tool_blocks else None,
        },
    }
