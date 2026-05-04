"""1-hour cache TTL — empirically supported on Bedrock for this model+region.

Anthropic's public API docs note that the `extended-cache-ttl-2025-04-11`
beta header (which gates 1h caching on the Anthropic API and Vertex) is
not accepted on Bedrock — see test_extended_ttl_header_rejected.py
("invalid beta flag"). On the basis of that note one might assume Bedrock
supports only 5m caching.

The actual Bedrock response data contradicts that assumption for
`global.anthropic.claude-opus-4-7` in `ap-northeast-2`: sending
`cache_control: {"type": "ephemeral", "ttl": "1h"}` *without* the beta
header is accepted, and the resulting usage breakdown places the prefix
into `ephemeral_1h_input_tokens` (not the 5m bucket).

This test pins that data-point-driven contract:
  * a unique per-run salt forces a cold cache, so the first call MUST
    perform a fresh write — we never accept a hot cache read as evidence
  * the fresh write MUST land in `ephemeral_1h_input_tokens`, not 5m
  * the second call MUST read it back

If a future Bedrock release demotes 1h to 5m, the assertion
`first.create_1h > 0 and first.create_5m == 0` will fail, surfacing the
contract change explicitly instead of silently passing.
"""
import secrets

from tests._base import usage_breakdown

NAME = "cache_ttl_1h"
DESCRIPTION = (
    "ttl='1h' on cold cache: fresh write lands in ephemeral_1h_input_tokens "
    "(not 5m); second call reads it back"
)

_PREFIX = "Detailed instructions follow. " * 1500


def run(client, model) -> dict:
    salt = secrets.token_hex(8)
    sys_blocks = [
        {
            "type": "text",
            "text": f"Run salt {salt}. " + _PREFIX + "Reply OK.",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    msg = [{"role": "user", "content": "reply OK"}]

    r1 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    u1, u2 = usage_breakdown(r1.usage), usage_breakdown(r2.usage)

    cold_start_verified = u1["create_total"] > 0 and u1["read_total"] == 0
    one_hour_bucket_populated = u1["create_1h"] > 0
    not_demoted_to_5m = u1["create_5m"] == 0
    second_call_reads_cache = u2["read_total"] > 0 and u2["create_total"] == 0

    contract_holds = (
        cold_start_verified
        and one_hour_bucket_populated
        and not_demoted_to_5m
        and second_call_reads_cache
    )

    if not cold_start_verified:
        err = ("salt failed to force cold start — first call did not perform a "
               "fresh write. Cannot evaluate 1h contract.")
    elif not one_hour_bucket_populated:
        err = ("ephemeral_1h_input_tokens == 0 on a fresh write — Bedrock "
               "appears to no longer route ttl='1h' into the 1h bucket.")
    elif not not_demoted_to_5m:
        err = ("ttl='1h' was silently demoted to 5m bucket on a fresh write.")
    elif not second_call_reads_cache:
        err = ("second call did not read the 1h cache back.")
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
                "not_demoted_to_5m_bucket": not_demoted_to_5m,
                "second_call_reads_cache": second_call_reads_cache,
            },
        },
        "error": err,
    }
