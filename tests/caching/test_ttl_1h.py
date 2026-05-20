"""Backcompat shim — actual probe lives in probes.caching.ttl_1h."""
from probes.caching.ttl_1h import NAME, DESCRIPTION, run  # noqa: F401
