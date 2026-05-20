"""PDF document + citations enabled → citation metadata is attached."""
import base64
import pathlib

NAME = "pdf_with_citations"
DESCRIPTION = "PDF base64 + citations:{enabled:true} returns at least one citation"

PDF = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "sample.pdf"


def run(client, model) -> dict:
    data = base64.standard_b64encode(PDF.read_bytes()).decode()
    resp = client.messages.create(
        model=model,
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": data,
                        },
                        "title": "Sample factbook",
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "text",
                        "text": "What single string is printed on the page? Cite the document.",
                    },
                ],
            }
        ],
    )
    cited = []
    for b in resp.content:
        if b.type == "text" and (getattr(b, "citations", None) or []):
            cited.append({"text": b.text[:60], "n": len(b.citations)})
    return {
        "ok": bool(cited),
        "info": {"cited_blocks": cited, "stop_reason": resp.stop_reason},
        "error": None if cited else "no citation metadata returned",
    }
