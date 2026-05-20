"""Backcompat shim — actual probe lives in probes.streaming.event_schema."""
from probes.streaming.event_schema import NAME, DESCRIPTION, run  # noqa: F401
