"""max_tokens limit triggers stop_reason=max_tokens when output exceeds budget."""
NAME = "max_tokens_truncation"
DESCRIPTION = "very small max_tokens forces stop_reason=max_tokens"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=4,
        messages=[{"role": "user", "content": "Write a 200-word essay about clouds."}],
    )
    return {
        "ok": resp.stop_reason == "max_tokens",
        "info": {"stop_reason": resp.stop_reason, "output_tokens": resp.usage.output_tokens},
    }
