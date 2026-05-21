"""metadata.user_id is accepted (advisory; not echoed back)."""
from probes._base import text_of

NAME = "metadata_user_id"
DESCRIPTION = "metadata={'user_id': ...} is accepted without 4xx"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=16,
        metadata={"user_id": "test-user-abc-123"},
        messages=[{"role": "user", "content": "Say 'metadata-ok'."}],
    )
    return {
        "ok": resp.stop_reason in ("end_turn", "stop_sequence"),
        "info": {"reply": text_of(resp)[:40], "stop_reason": resp.stop_reason},
    }
