"""Korean prompt → Korean reply with characters in the Hangul range."""
from probes._base import text_of

NAME = "multilingual_korean"
DESCRIPTION = "Korean prompt yields a reply containing Hangul characters"


def _has_hangul(s: str) -> bool:
    return any("가" <= ch <= "힣" for ch in s)


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[
            {
                "role": "user",
                "content": "한국어로 인사를 한 문장으로 짧게 작성해주세요.",
            }
        ],
    )
    txt = text_of(resp)
    return {
        "ok": _has_hangul(txt) and resp.stop_reason in ("end_turn", "stop_sequence"),
        "info": {"reply": txt[:80]},
    }
