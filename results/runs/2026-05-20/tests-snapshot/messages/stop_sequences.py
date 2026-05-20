"""Custom stop_sequences halt generation and surface in stop_reason."""
from probes._base import text_of

NAME = "stop_sequences"
DESCRIPTION = "stop_sequences trigger stop_reason=stop_sequence"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        stop_sequences=["END"],
        messages=[
            {
                "role": "user",
                "content": "Write the letters A B C then the word END then more letters.",
            }
        ],
    )
    return {
        "ok": resp.stop_reason == "stop_sequence" and resp.stop_sequence == "END",
        "info": {
            "stop_reason": resp.stop_reason,
            "stop_sequence": resp.stop_sequence,
            "preview": text_of(resp)[:60],
        },
    }
