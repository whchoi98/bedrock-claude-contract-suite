"""Multiple image blocks in one user turn."""
import base64
import pathlib

from probes._base import text_of

NAME = "vision_multi_image"
DESCRIPTION = "two inline images in one turn; model distinguishes them"

IMG = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "red_4x4.png"


def run(client, model) -> dict:
    data_red = base64.standard_b64encode(IMG.read_bytes()).decode()
    # Build a tiny green PNG inline (avoids extra fixture).
    import struct, zlib
    def png(rgb):
        sig = b"\x89PNG\r\n\x1a\n"
        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t+d) & 0xffffffff)
        ihdr = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
        raw = b""
        for _ in range(4):
            raw += b"\x00" + bytes(rgb) * 4
        return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    data_green = base64.standard_b64encode(png((0, 255, 0))).decode()

    def img_block(d):
        return {"type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": d}}

    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[
            {
                "role": "user",
                "content": [
                    img_block(data_red),
                    img_block(data_green),
                    {"type": "text",
                     "text": "There are two images. Reply with the colors in order, "
                             "comma separated, lowercase."},
                ],
            }
        ],
    )
    txt = text_of(resp).lower()
    return {
        "ok": "red" in txt and "green" in txt,
        "info": {"reply": txt[:60],
                 "order_red_first": txt.find("red") < txt.find("green")},
    }
