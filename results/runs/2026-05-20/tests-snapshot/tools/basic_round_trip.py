"""Two-step tool use: model emits tool_use, then synthesizes after tool_result."""
from probes._base import text_of

NAME = "tool_use"
DESCRIPTION = "model selects a tool, then composes a final answer from tool_result"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]


def run(client, model) -> dict:
    user_msg = {"role": "user", "content": "What's the weather in Seoul? Use the tool."}
    r1 = client.messages.create(
        model=model, max_tokens=256, tools=TOOLS, messages=[user_msg]
    )
    tool_blocks = [b for b in r1.content if b.type == "tool_use"]
    if not tool_blocks or r1.stop_reason != "tool_use":
        return {
            "ok": False,
            "info": {"stop_reason": r1.stop_reason, "blocks": [b.type for b in r1.content]},
            "error": "model did not request tool",
        }
    tu = tool_blocks[0]

    # Step 2: feed back a fabricated tool_result and ask for the final answer.
    r2 = client.messages.create(
        model=model,
        max_tokens=128,
        tools=TOOLS,
        messages=[
            user_msg,
            {"role": "assistant", "content": r1.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": "Sunny, 21C",
                    }
                ],
            },
        ],
    )
    final = text_of(r2)
    return {
        "ok": r2.stop_reason == "end_turn" and ("21" in final or "sunny" in final.lower()),
        "info": {
            "tool_called": tu.name,
            "tool_input": dict(tu.input),
            "final": final[:80],
            "stop_reason": r2.stop_reason,
        },
    }
