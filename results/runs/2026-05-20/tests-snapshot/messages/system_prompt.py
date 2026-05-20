"""System prompt is honored (string form and structured-blocks form)."""
from probes._base import text_of

NAME = "system_prompt"
DESCRIPTION = "system prompt steers reply style (string + blocks form)"


def run(client, model) -> dict:
    # Form 1: plain string
    r1 = client.messages.create(
        model=model,
        max_tokens=32,
        system="Always reply in uppercase.",
        messages=[{"role": "user", "content": "say hello"}],
    )
    t1 = text_of(r1)

    # Form 2: list of system blocks
    r2 = client.messages.create(
        model=model,
        max_tokens=32,
        system=[{"type": "text", "text": "Always reply in lowercase."}],
        messages=[{"role": "user", "content": "SAY HELLO"}],
    )
    t2 = text_of(r2)

    upper_ok = any(c.isalpha() for c in t1) and t1 == t1.upper()
    lower_ok = any(c.isalpha() for c in t2) and t2 == t2.lower()
    return {
        "ok": upper_ok and lower_ok,
        "info": {"upper_reply": t1[:40], "lower_reply": t2[:40]},
    }
