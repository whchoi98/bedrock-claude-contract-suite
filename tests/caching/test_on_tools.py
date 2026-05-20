"""Backcompat shim — actual probe lives in probes.caching.on_tools."""
from probes.caching.on_tools import NAME, DESCRIPTION, run  # noqa: F401
