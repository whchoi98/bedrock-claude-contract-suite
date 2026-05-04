"""Mixed 5m + 1h breakpoints in the same request — both buckets populate.

Empirical contract on Bedrock: when a single request contains a 1h-tagged
block AND a 5m-tagged block, the cold-start fresh write places tokens
into BOTH `ephemeral_1h_input_tokens` and `ephemeral_5m_input_tokens`
separately — proving the API tracks the two buckets independently. A
unique per-run salt forces a cold cache; the first call must be a fresh
write and both buckets must be non-zero on it.
"""
import secrets

from tests._base import usage_breakdown

NAME = "cache_ttl_mixed_5m_and_1h"
DESCRIPTION = (
    "5m + 1h in same request on cold cache: BOTH ephemeral_1h and "
    "ephemeral_5m populate on the fresh write; second call reads the sum"
)

_PREFIX_A = "Stable corpus A. " * 1500
_PREFIX_B = "Reference data B. " * 1500


def run(client, model) -> dict:
    salt = secrets.token_hex(8)
    sys_blocks = [
        {
            "type": "text",
            "text": f"salt={salt}. " + _PREFIX_A,
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    msg = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"salt={salt}. " + _PREFIX_B,
                    "cache_control": {"type": "ephemeral", "ttl": "5m"},
                },
                {"type": "text", "text": "Reply 'mixed-ok'."},
            ],
        }
    ]

    r1 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)
    u1, u2 = usage_breakdown(r1.usage), usage_breakdown(r2.usage)

    cold_start_verified = u1["create_total"] > 0 and u1["read_total"] == 0
    one_hour_bucket_populated = u1["create_1h"] > 0
    five_minute_bucket_populated = u1["create_5m"] > 0
    second_call_reads_back_full_prefix = (
        u2["read_total"] > 0 and u2["read_total"] >= u1["create_total"]
    )

    contract_holds = (
        cold_start_verified
        and one_hour_bucket_populated
        and five_minute_bucket_populated
        and second_call_reads_back_full_prefix
    )

    if not cold_start_verified:
        err = "salt failed to force cold start — first call did not perform a fresh write."
    elif not one_hour_bucket_populated:
        err = "ephemeral_1h_input_tokens == 0 on cold-start mixed request — 1h facet appears dropped."
    elif not five_minute_bucket_populated:
        err = "ephemeral_5m_input_tokens == 0 on cold-start mixed request."
    elif not second_call_reads_back_full_prefix:
        err = "second call did not read back the full cached prefix."
    else:
        err = None

    return {
        "ok": contract_holds,
        "info": {
            "contract": "supported",
            "first": u1,
            "second": u2,
            "salt": salt,
            "evidence": {
                "cold_start_verified": cold_start_verified,
                "one_hour_bucket_populated_on_fresh_write": one_hour_bucket_populated,
                "five_minute_bucket_populated_on_fresh_write": five_minute_bucket_populated,
                "second_call_reads_back_full_prefix": second_call_reads_back_full_prefix,
            },
        },
        "error": err,
    }
