"""Claude Platform on AWS provider — uses the official `AnthropicAWS` client.

Endpoint: https://aws-external-anthropic.{region}.api.aws  (auto-derived)
Auth:     ANTHROPIC_AWS_API_KEY → sent as x-api-key (SigV4 also supported but
          not used by this suite; see results/sdk_comparison.md §D).
Workspace: ANTHROPIC_AWS_WORKSPACE_ID → sent as anthropic-workspace-id header.

The official SDK (`anthropic.AnthropicAWS`, in beta) auto-resolves base_url,
workspace_id, region, and auth mode from constructor arguments or environment
variables. We pass them explicitly so the suite's `--providers cpaws` runs
are reproducible regardless of ambient AWS credentials. See
`results/sdk_comparison.md` for the full Anthropic vs AnthropicAWS contrast.
"""
import os
import sys
from anthropic import AnthropicAWS


def make_client(region: str) -> AnthropicAWS:
    api_key = os.environ.get("ANTHROPIC_AWS_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")
    if not api_key:
        print("ERROR: ANTHROPIC_AWS_API_KEY not set.", file=sys.stderr)
        sys.exit(2)
    if not workspace_id:
        print("ERROR: ANTHROPIC_AWS_WORKSPACE_ID not set.", file=sys.stderr)
        sys.exit(2)
    return AnthropicAWS(
        api_key=api_key,
        workspace_id=workspace_id,
        aws_region=region,
    )
