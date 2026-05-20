"""PDF document input via a base64 document block."""
import base64
import pathlib

from probes._base import text_of

NAME = "pdf_document"
DESCRIPTION = "document content block (PDF base64) is parsed and answerable"

PDF_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "sample.pdf"


def run(client, model) -> dict:
    data = base64.standard_b64encode(PDF_PATH.read_bytes()).decode()
    resp = client.messages.create(
        model=model,
        max_tokens=64,
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
                    },
                    {
                        "type": "text",
                        "text": "What single string is printed on the page? Reply with just that string.",
                    },
                ],
            }
        ],
    )
    txt = text_of(resp)
    return {
        "ok": "BEDROCK_OPUS_PDF_OK" in txt,
        "info": {"reply": txt[:80], "stop_reason": resp.stop_reason},
    }
