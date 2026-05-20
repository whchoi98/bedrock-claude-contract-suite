"""Japanese prompt → reply containing Hiragana / Katakana / Kanji."""
from probes._base import text_of

NAME = "multilingual_japanese"
DESCRIPTION = "Japanese prompt yields a reply with Japanese script"


def _has_jp(s: str) -> bool:
    for ch in s:
        if ("぀" <= ch <= "ヿ") or ("一" <= ch <= "鿿"):
            return True
    return False


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[{"role": "user", "content": "日本語で短い挨拶を一文だけ書いてください。"}],
    )
    txt = text_of(resp)
    return {
        "ok": _has_jp(txt) and resp.stop_reason in ("end_turn", "stop_sequence"),
        "info": {"reply": txt[:80]},
    }
