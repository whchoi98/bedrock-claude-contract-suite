"""Backcompat shim — actual probe lives in probes.caching.ttl_mixed."""
from probes.caching.ttl_mixed import NAME, DESCRIPTION, run  # noqa: F401
