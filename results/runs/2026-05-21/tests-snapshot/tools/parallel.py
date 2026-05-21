"""Parallel tool use: a single response should contain multiple tool_use blocks."""
NAME = "parallel_tool_use"
DESCRIPTION = "model returns multiple tool_use blocks in one response"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        tools=TOOLS,
        messages=[
            {
                "role": "user",
                "content": "Get the weather for Seoul, Tokyo, and Sydney. "
                           "Call the tool once for each city, in parallel.",
            }
        ],
    )
    tu_blocks = [b for b in resp.content if b.type == "tool_use"]
    cities = sorted(b.input.get("city", "").lower() for b in tu_blocks)
    return {
        "ok": len(tu_blocks) >= 2,
        "info": {
            "tool_use_count": len(tu_blocks),
            "cities": cities,
            "stop_reason": resp.stop_reason,
        },
    }
