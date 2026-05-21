"""tool_result content may include image blocks (multimodal tool output)."""
import base64
import pathlib

NAME = "tool_result_image"
DESCRIPTION = "tool_result with image content is accepted"

IMG = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "red_4x4.png"
TOOLS = [
    {
        "name": "render",
        "description": "Render an image.",
        "input_schema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
        },
    }
]


def run(client, model) -> dict:
    user_msg = {"role": "user", "content": "Use 'render' to make an image of a red square."}
    r1 = client.messages.create(model=model, max_tokens=256, tools=TOOLS, messages=[user_msg])
    tu = next((b for b in r1.content if b.type == "tool_use"), None)
    if tu is None:
        return {"ok": False, "info": {"stop_reason": r1.stop_reason}, "error": "no tool_use"}

    data = base64.standard_b64encode(IMG.read_bytes()).decode()
    r2 = client.messages.create(
        model=model,
        max_tokens=64,
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
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": data,
                                },
                            }
                        ],
                    },
                    {"type": "text", "text": "What single color dominates the image? One word."},
                ],
            },
        ],
    )
    txt = "".join(b.text for b in r2.content if b.type == "text").lower()
    return {
        "ok": "red" in txt,
        "info": {"reply": txt[:60], "stop_reason": r2.stop_reason},
    }
