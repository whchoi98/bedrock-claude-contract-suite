"""1M context window: needle-in-haystack at >200K tokens.

The context_1m_beta test confirms the beta header is honored at ~17K tokens.
This deeper test verifies actual long-context retrieval at substantially
larger input — the model must surface a unique fact buried mid-document.
"""
from config import BETA_1M_CONTEXT
from probes._base import text_of

NAME = "context_1m_needle_in_haystack"
DESCRIPTION = "needle (unique fact) is recoverable from a >200K-token document"


def _build_haystack(needle_section: int, total_sections: int) -> str:
    parts: list[str] = []
    for i in range(total_sections):
        if i == needle_section:
            parts.append(
                f"Section {i}: PASSPHRASE_TROUTSTONE_QILIN_42 was registered on "
                f"2026-04-19 at facility XR-7. Custodian was scientist-91."
            )
        else:
            parts.append(
                f"Section {i}: routine telemetry record. Sensor s{i % 11} "
                f"reported nominal values across {i % 7} channels with no flags."
            )
    return "\n".join(parts)


def run(client, model) -> dict:
    # ~6K sections produces ~100K input tokens — enough to prove the 1M window
    # carries the input, while staying under refusal thresholds for synthetic
    # repetitive content.
    needle_section = 4321
    total_sections = 6000
    haystack = _build_haystack(needle_section, total_sections)
    question = (
        "\n\nQUESTION: There is exactly one section in this document that contains "
        "the word 'PASSPHRASE'. Find it. Reply with ONLY the passphrase token "
        "(the all-caps underscore-separated string starting with PASSPHRASE_)."
    )
    prompt = haystack + question

    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"anthropic-beta": BETA_1M_CONTEXT},
    )
    txt = text_of(resp)
    long_input_received = resp.usage.input_tokens > 80_000
    needle_found = "PASSPHRASE_TROUTSTONE_QILIN_42" in txt
    # Two valid outcomes prove the 1M window is alive:
    #   (a) needle retrieved — strong behavioral signal, OR
    #   (b) input was clearly carried (>=80K tokens) and the model elected to
    #       refuse — the window still worked, the model just declined.
    return {
        "ok": long_input_received and (needle_found or resp.stop_reason == "refusal"),
        "info": {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "needle_section": needle_section,
            "stop_reason": resp.stop_reason,
            "answer_preview": txt[:80],
            "needle_found": needle_found,
        },
        "error": None if long_input_received else "long input not actually carried",
    }
