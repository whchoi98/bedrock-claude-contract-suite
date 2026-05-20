"""Backcompat shim — actual probe lives in probes.messages.create."""
from probes.messages.create import NAME, DESCRIPTION, run  # noqa: F401
