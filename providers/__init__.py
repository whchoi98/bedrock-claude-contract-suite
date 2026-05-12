"""Provider abstraction — factory and model-alias resolver.

A "provider" is an API surface that hosts Anthropic Claude:
  - "bedrock" → AnthropicBedrock against bedrock-runtime
  - "cpaws"   → Anthropic SDK against aws-external-anthropic

An "alias" is a human-friendly model identifier ("opus-4-7"). The resolver
maps (provider, alias) → concrete provider-specific model ID.
"""
import os

from config import MODEL_ALIASES, PROVIDERS, REGION


def make_client(provider: str):
    """Construct a client for the given provider.

    bedrock → uses config.REGION (AWS_REGION).
    cpaws   → uses CPAWS_REGION env, falls back to config.REGION.
    """
    if provider == "bedrock":
        from .bedrock import make_client as _make
        return _make(REGION)
    if provider == "cpaws":
        from .cpaws import make_client as _make
        cpaws_region = os.environ.get("CPAWS_REGION", REGION)
        return _make(cpaws_region)
    raise ValueError(
        f"unknown provider {provider!r}; valid: {list(PROVIDERS)}"
    )


def resolve_model(provider: str, alias: str) -> str:
    """Return the concrete model ID for (provider, alias)."""
    if provider not in PROVIDERS:
        raise ValueError(
            f"unknown provider {provider!r}; valid: {list(PROVIDERS)}"
        )
    mapping = MODEL_ALIASES.get(alias)
    if mapping is None:
        raise ValueError(
            f"unknown model alias {alias!r}; "
            f"valid: {list(MODEL_ALIASES.keys())}"
        )
    model_id = mapping.get(provider)
    if model_id is None:
        raise ValueError(
            f"alias {alias!r} not mapped for provider {provider!r}"
        )
    return model_id
