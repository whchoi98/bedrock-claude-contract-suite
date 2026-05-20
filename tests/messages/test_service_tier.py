"""Backcompat shim — actual probe lives in probes.messages.service_tier."""
from probes.messages.service_tier import NAME, DESCRIPTION, run  # noqa: F401
