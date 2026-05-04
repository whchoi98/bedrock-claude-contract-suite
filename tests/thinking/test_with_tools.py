"""Thinking + tool use combined: signature must be preserved across the round trip."""
NAME = "thinking_with_tools"
DESCRIPTION = "thinking + tool_use round trip preserves thinking block signature"

TOOLS = [
    {
        "name": "compute",
        "description": "Compute integer division.",
        "input_schema": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    }
]


def run(client, model) -> dict:
    msg = [{"role": "user", "content": "Compute 10000 // 7 using the tool, then explain."}]
    r1 = client.messages.create(
        model=model,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        extra_body={"output_config": {"effort": "medium"}},
        tools=TOOLS,
        messages=msg,
    )
    tu = next((b for b in r1.content if b.type == "tool_use"), None)
    if tu is None:
        return {"ok": False, "info": {"blocks": [b.type for b in r1.content]},
                "error": "model did not call the tool"}

    r2 = client.messages.create(
        model=model,
        max_tokens=512,
        thinking={"type": "adaptive"},
        extra_body={"output_config": {"effort": "low"}},
        tools=TOOLS,
        messages=[
            *msg,
            {"role": "assistant", "content": r1.content},
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tu.id, "content": "1428"}
                ],
            },
        ],
    )
    final_text = "".join(b.text for b in r2.content if b.type == "text")
    return {
        "ok": "1428" in final_text and r2.stop_reason == "end_turn",
        "info": {
            "first_blocks": [b.type for b in r1.content],
            "tool_input": dict(tu.input),
            "final_preview": final_text[:80],
        },
    }
