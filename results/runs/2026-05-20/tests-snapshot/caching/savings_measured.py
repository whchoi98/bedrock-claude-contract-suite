"""Caching must actually reduce billable input tokens.

When a request is served from cache, `usage.input_tokens` should drop
substantially and `cache_read_input_tokens` should account for the bulk
of the original prefix size.
"""
NAME = "cache_savings_measured"
DESCRIPTION = "cached call: input_tokens collapses; cache_read carries the prefix bulk"


def _u(u) -> dict:
    return {
        "input": u.input_tokens,
        "create": getattr(u, "cache_creation_input_tokens", 0),
        "read": getattr(u, "cache_read_input_tokens", 0),
    }


def run(client, model) -> dict:
    big_prefix = "Stable reference corpus. " * 1500  # ~9K tokens
    sys_blocks = [
        {"type": "text", "text": big_prefix + "Reply OK.",
         "cache_control": {"type": "ephemeral"}}
    ]
    msg = [{"role": "user", "content": "reply OK"}]

    # Two consecutive calls with the same cached prefix.
    r1 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    u1, u2 = _u(r1.usage), _u(r2.usage)

    cache_volume = max(u1["create"], u1["read"], u2["read"])
    # Billable input on a cached call should be a small fraction of the full prefix.
    billable_ratio = u2["input"] / cache_volume if cache_volume else 1.0
    saved_substantial = cache_volume >= 5000 and billable_ratio < 0.05
    return {
        "ok": saved_substantial,
        "info": {
            "first": u1, "second": u2,
            "cache_volume": cache_volume,
            "billable_input_on_2nd_call": u2["input"],
            "billable_ratio": round(billable_ratio, 4),
        },
        "error": None if saved_substantial
                 else f"savings insufficient: ratio={billable_ratio:.3f}",
    }
