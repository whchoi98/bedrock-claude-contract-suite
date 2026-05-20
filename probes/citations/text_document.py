"""Citations: enable citations on a text-document block, expect citation metadata."""
NAME = "citations"
DESCRIPTION = "document citations={enabled:true} produces citation entries on text blocks"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": (
                                "Project Aurora launched on 2024-03-12. "
                                "Lead engineer was Mei Tanaka. "
                                "Initial budget was 2.4 million USD."
                            ),
                        },
                        "title": "Aurora factbook",
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "text",
                        "text": "Who led Project Aurora? Cite the source.",
                    },
                ],
            }
        ],
    )
    cited_blocks = []
    for b in resp.content:
        if b.type == "text":
            cites = getattr(b, "citations", None) or []
            if cites:
                cited_blocks.append({"text": b.text[:60], "citation_count": len(cites)})
    return {
        "ok": bool(cited_blocks),
        "info": {"cited_blocks": cited_blocks, "stop_reason": resp.stop_reason},
        "error": None if cited_blocks else "no citation metadata returned",
    }
