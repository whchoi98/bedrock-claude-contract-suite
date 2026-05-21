"""Vision: inline base64 image in a user turn."""
import base64
import pathlib

from probes._base import text_of

NAME = "vision"
DESCRIPTION = "model accepts an inline base64 PNG and describes it"

IMG_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "red_4x4.png"


def run(client, model) -> dict:
    data = base64.standard_b64encode(IMG_PATH.read_bytes()).decode()
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": data,
                        },
                    },
                    {"type": "text", "text": "What single color dominates this image? One word."},
                ],
            }
        ],
    )
    txt = text_of(resp).lower()
    return {
        "ok": "red" in txt,
        "info": {"reply": txt[:60], "stop_reason": resp.stop_reason},
    }
