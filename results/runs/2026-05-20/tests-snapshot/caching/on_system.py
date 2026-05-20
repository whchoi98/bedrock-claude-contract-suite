"""Prompt caching: a 2nd call with the same cached prefix should hit cache."""
NAME = "prompt_caching"
DESCRIPTION = "cache_control marks a system prefix; 2nd call shows cache_read_input_tokens"


def _build_long_system() -> list[dict]:
    # Empirically Opus 4.7 needs a substantially large prefix for the cache to
    # actually retain it; 13K tokens reliably triggers cache_create + cache_read.
    body = (
        "You are a meticulous assistant. " * 1500
        + "When asked, reply with 'CACHED_OK'."
    )
    return [{"type": "text", "text": body, "cache_control": {"type": "ephemeral"}}]


def _usage_dict(u) -> dict:
    return {
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0),
    }


def run(client, model) -> dict:
    sys_blocks = _build_long_system()
    msg = [{"role": "user", "content": "Reply with CACHED_OK."}]

    r1 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)

    u1 = _usage_dict(r1.usage)
    u2 = _usage_dict(r2.usage)
    # Caching is "alive" if either:
    #   (a) we created a cache entry on call #1 AND read it on call #2, OR
    #   (b) the cache was already hot (created in a previous run) AND both calls
    #       served from cache_read.
    fresh = u1["cache_creation_input_tokens"] > 0 and u2["cache_read_input_tokens"] > 0
    hot = u1["cache_read_input_tokens"] > 0 and u2["cache_read_input_tokens"] > 0
    return {
        "ok": fresh or hot,
        "info": {"first_call_usage": u1, "second_call_usage": u2,
                 "path": "fresh" if fresh else ("hot" if hot else "none")},
        "error": None if (fresh or hot) else "no cache create or read observed",
    }
