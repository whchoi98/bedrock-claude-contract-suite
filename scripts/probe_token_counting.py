"""Probe token counting on Bedrock — Invoke API vs Anthropic-shape path.

Tests three access paths per model, in parallel:
  V1. SDK client.messages.count_tokens() (Anthropic SDK layer)
  V2. Direct HTTP POST /model/{id}/count-tokens (AWS-native CountTokens)
  V3. Direct HTTP POST /v1/messages/count_tokens (Anthropic-shape path)
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from anthropic import AnthropicError

from client import make_client
from config import ALL_MODELS, REGION

INVOKE_BASE = f"https://bedrock-runtime.{REGION}.amazonaws.com"
MSG = [{"role": "user", "content": "How many tokens does this message contain?"}]


def _bearer_token() -> str:
    tok = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    if not tok:
        print("ERROR: AWS_BEARER_TOKEN_BEDROCK not set.", file=sys.stderr)
        sys.exit(2)
    return tok


def v1_sdk_invoke(client, model: str) -> dict:
    try:
        out = client.messages.count_tokens(model=model, messages=MSG)
        return {"ok": True, "input_tokens": out.input_tokens}
    except AnthropicError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"}


def _raw_post(url: str, body: dict) -> dict:
    try:
        r = httpx.post(url, headers={
            "Authorization": f"Bearer {_bearer_token()}",
            "Content-Type": "application/json",
        }, json=body, timeout=30.0)
        return {"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:300]}
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}


def v2_raw_invoke_count(model: str) -> dict:
    return _raw_post(
        f"{INVOKE_BASE}/model/{model}/count-tokens",
        {"messages": MSG, "anthropic_version": "bedrock-2023-05-31"},
    )


def v3_raw_anthropic_count(model: str) -> dict:
    return _raw_post(
        f"{INVOKE_BASE}/v1/messages/count_tokens",
        {"model": model, "messages": MSG},
    )


def probe_model(client, model: str) -> dict:
    with ThreadPoolExecutor(max_workers=3) as ex:
        v1 = ex.submit(v1_sdk_invoke, client, model)
        v2 = ex.submit(v2_raw_invoke_count, model)
        v3 = ex.submit(v3_raw_anthropic_count, model)
        return {"V1_sdk_invoke": v1.result(),
                "V2_raw_invoke_path": v2.result(),
                "V3_raw_anthropic_path": v3.result()}


def main() -> int:
    client = make_client()
    results: dict = {"region": REGION, "by_model": {}}
    for model in ALL_MODELS:
        print(f"\n=== {model} ===")
        per_model = probe_model(client, model)
        results["by_model"][model] = per_model
        for label, r in [("V1 SDK→Invoke", per_model["V1_sdk_invoke"]),
                         ("V2 raw /model/{id}/count-tokens", per_model["V2_raw_invoke_path"]),
                         ("V3 raw /v1/messages/count_tokens", per_model["V3_raw_anthropic_path"])]:
            mark = "OK " if r["ok"] else "RJ "
            preview = r.get("error") or r.get("body") or json.dumps(r)
            print(f"  {mark} {label:<40s} {preview[:160]}")

    out = pathlib.Path(__file__).resolve().parent.parent / "results" / "token_counting_probe.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
