"""Factory for the AnthropicBedrock client.

Reads the Bedrock API key from AWS_BEARER_TOKEN_BEDROCK and the region from config.
"""
import os
import sys
from anthropic import AnthropicBedrock

from config import REGION


def make_client() -> AnthropicBedrock:
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("ERROR: AWS_BEARER_TOKEN_BEDROCK not set.", file=sys.stderr)
        sys.exit(2)
    return AnthropicBedrock(aws_region=REGION)
