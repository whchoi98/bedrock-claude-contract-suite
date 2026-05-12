"""Claude Platform on AWS provider — Anthropic SDK with custom base_url and
workspace API key authentication.

Endpoint: https://aws-external-anthropic.{region}.api.aws
Auth: ANTHROPIC_AWS_API_KEY → sent as x-api-key
Required header: anthropic-workspace-id (from ANTHROPIC_AWS_WORKSPACE_ID)
"""
import os
import sys
from anthropic import Anthropic


def make_client(region: str) -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    if not api_key:
        print("ERROR: ANTHROPIC_AWS_API_KEY not set.", file=sys.stderr)
        sys.exit(2)
    if not workspace_id:
        print("ERROR: ANTHROPIC_AWS_WORKSPACE_ID not set.", file=sys.stderr)
        sys.exit(2)
    return Anthropic(
        base_url=f"https://aws-external-anthropic.{region}.api.aws",
        api_key=api_key,
        default_headers={"anthropic-workspace-id": workspace_id},
    )
