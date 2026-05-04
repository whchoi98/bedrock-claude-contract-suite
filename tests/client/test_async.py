"""AsyncAnthropicBedrock: same call from the async client."""
import asyncio
import os

from anthropic import AsyncAnthropicBedrock

from config import REGION

NAME = "async_client"
DESCRIPTION = "AsyncAnthropicBedrock returns a valid Message"


def run(_client, model) -> dict:
    async def _go():
        async with AsyncAnthropicBedrock(aws_region=REGION) as ac:
            return await ac.messages.create(
                model=model,
                max_tokens=16,
                messages=[{"role": "user", "content": "Say 'async-ok'."}],
            )

    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return {"ok": False, "info": {}, "error": "no bearer token"}
    resp = asyncio.run(_go())
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "ok": resp.stop_reason in ("end_turn", "stop_sequence") and "async" in text.lower(),
        "info": {"reply": text[:40], "stop_reason": resp.stop_reason},
    }
