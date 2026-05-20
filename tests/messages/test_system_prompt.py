"""Backcompat shim — actual probe lives in probes.messages.system_prompt."""
from probes.messages.system_prompt import NAME, DESCRIPTION, run  # noqa: F401
