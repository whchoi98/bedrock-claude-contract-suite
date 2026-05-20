"""Backcompat shim — actual probe lives in probes.caching.on_messages."""
from probes.caching.on_messages import NAME, DESCRIPTION, run  # noqa: F401
