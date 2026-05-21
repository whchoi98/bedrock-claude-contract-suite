"""Async client equivalence — provider-agnostic.

Verifies that the async counterpart of whichever client the runner injected
produces a valid Message with the same model. Dispatch by client class so
the test works under both `--providers bedrock` and `--providers cpaws`.

Earlier revisions hardcoded `AsyncAnthropicBedrock` which spuriously failed
on CPaws (CPaws model ID rejected by bedrock-runtime).
"""
import asyncio
import os

from anthropic import (
    AnthropicAWS,
    AnthropicBedrock,
    AsyncAnthropicAWS,
    AsyncAnthropicBedrock,
)

NAME = "async_client"
DESCRIPTION = "Async client returns a valid Message on the same provider"


def _make_async_counterpart(client):
    """Build the async client matching the sync client's provider + auth."""
    if isinstance(client, AnthropicBedrock):
        return AsyncAnthropicBedrock(aws_region=os.environ.get("AWS_REGION", "ap-northeast-2"))
    if isinstance(client, AnthropicAWS):
        return AsyncAnthropicAWS(
            api_key=os.environ["ANTHROPIC_AWS_API_KEY"],
            workspace_id=os.environ["ANTHROPIC_AWS_WORKSPACE_ID"],
            aws_region=os.environ.get("CPAWS_REGION")
                       or os.environ.get("AWS_REGION", "ap-northeast-2"),
        )
    raise TypeError(
        f"Unsupported client type for async test: {type(client).__name__}"
    )


def run(client, model) -> dict:
    async def _go():
        async with _make_async_counterpart(client) as ac:
            return await ac.messages.create(
                model=model,
                max_tokens=16,
                messages=[{"role": "user", "content": "Say 'async-ok'."}],
            )

    resp = asyncio.run(_go())
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "ok": resp.stop_reason in ("end_turn", "stop_sequence") and "async" in text.lower(),
        "info": {
            "reply": text[:40],
            "stop_reason": resp.stop_reason,
            "client_class": type(client).__name__,
        },
    }
