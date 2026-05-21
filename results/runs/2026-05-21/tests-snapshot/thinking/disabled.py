"""thinking.type=disabled produces no thinking block."""
NAME = "thinking_disabled"
DESCRIPTION = "thinking={type:disabled} returns text-only response"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": "What is 2+2? Number only."}],
    )
    blocks = [b.type for b in resp.content]
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "ok": "thinking" not in blocks and "4" in text,
        "info": {"blocks": blocks, "text": text[:40]},
    }
