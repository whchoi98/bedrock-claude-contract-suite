"""Backward-compat shim — keep `from client import make_client` working.

New code should call `providers.make_client(provider)` directly.
"""
from providers import make_client as _make_client


def make_client():
    """Construct the default-provider client (Bedrock)."""
    return _make_client("bedrock")
