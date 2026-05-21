"""Multi-turn conversation: assistant remembers prior turn."""
from probes._base import text_of

NAME = "multi_turn"
DESCRIPTION = "assistant uses prior-turn context to answer follow-up"


def run(client, model) -> dict:
    history = [
        {"role": "user", "content": "My name is Daisy."},
        {"role": "assistant", "content": "Nice to meet you, Daisy."},
        {"role": "user", "content": "What is my name? Reply with just the name."},
    ]
    resp = client.messages.create(model=model, max_tokens=16, messages=history)
    txt = text_of(resp).strip().rstrip(".").lower()
    return {
        "ok": "daisy" in txt,
        "info": {"reply": text_of(resp)[:40]},
    }
