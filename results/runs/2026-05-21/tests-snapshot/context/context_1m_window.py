"""1M context-window beta header is accepted."""
from config import BETA_1M_CONTEXT
from probes._base import text_of

NAME = "context_1m_beta"
DESCRIPTION = "anthropic-beta: context-1m-2025-08-07 accepted; long input round-trips"


def run(client, model) -> dict:
    # Build a believable long document so the model engages instead of refusing.
    paragraphs = []
    for i in range(400):
        paragraphs.append(
            f"Section {i}: In our internal report, milestone M{i} was reached on "
            f"day {i*3 % 365}. Owner was engineer-{i % 17}. Risk level was "
            f"{['low','medium','high'][i % 3]}."
        )
    document = "\n".join(paragraphs)
    question = (
        "\n\nQUESTION: In Section 42, who was the owner? "
        "Reply with exactly 'engineer-N' where N is the number."
    )

    resp = client.messages.create(
        model=model,
        max_tokens=32,
        messages=[{"role": "user", "content": document + question}],
        extra_headers={"anthropic-beta": BETA_1M_CONTEXT},
    )
    txt = text_of(resp)
    expected_owner = f"engineer-{42 % 17}"  # 8
    return {
        "ok": expected_owner in txt and resp.usage.input_tokens > 5000,
        "info": {
            "input_tokens": resp.usage.input_tokens,
            "stop_reason": resp.stop_reason,
            "expected": expected_owner,
            "preview": txt[:60],
        },
    }
