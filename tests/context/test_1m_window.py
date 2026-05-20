"""Backcompat shim — actual probe lives in probes.context.context_1m_window."""
from probes.context.context_1m_window import NAME, DESCRIPTION, run  # noqa: F401
