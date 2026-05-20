"""Backcompat shim — actual probe lives in probes.client.async_client."""
from probes.client.async_client import NAME, DESCRIPTION, run  # noqa: F401
