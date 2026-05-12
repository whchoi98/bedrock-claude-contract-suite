"""Bedrock provider — AnthropicBedrock client using AWS_BEARER_TOKEN_BEDROCK."""
import os
import sys
from anthropic import AnthropicBedrock


def make_client(region: str) -> AnthropicBedrock:
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("ERROR: AWS_BEARER_TOKEN_BEDROCK not set.", file=sys.stderr)
        sys.exit(2)
    return AnthropicBedrock(aws_region=region)
