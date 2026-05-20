"""search_result citations must point to the CORRECT source.

Two distinct search_result blocks. Question is answerable only from the
second one. The model's answer must contain "Mei Tanaka" AND the citation
metadata must reference the team source URL — not the unrelated launch URL.
"""
NAME = "citations_search_result_correct_source"
DESCRIPTION = "answer mentions Mei Tanaka AND citation points at the team source"

LAUNCH_URL = "https://example.com/aurora"
TEAM_URL = "https://example.com/aurora-team"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "search_result",
                        "source": LAUNCH_URL,
                        "title": "Project Aurora launch",
                        "content": [{"type": "text",
                                     "text": "Project Aurora launched on 2024-03-12."}],
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "search_result",
                        "source": TEAM_URL,
                        "title": "Aurora team",
                        "content": [{"type": "text",
                                     "text": "Lead engineer was Mei Tanaka."}],
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "text",
                        "text": "Who led Project Aurora? Cite the document that supports your answer.",
                    },
                ],
            }
        ],
    )
    answer = "".join(b.text for b in resp.content if b.type == "text")
    cited_sources: list[str] = []
    for b in resp.content:
        if b.type == "text":
            for c in (getattr(b, "citations", None) or []):
                src = getattr(c, "source", None) or getattr(c, "document_source", None) \
                       or getattr(c, "url", None)
                # SDK exposes search_result citations with `source` attr; fall back to dict.
                if src is None and hasattr(c, "model_dump"):
                    src = c.model_dump().get("source") or c.model_dump().get("url")
                if src:
                    cited_sources.append(src)

    answer_correct = "Mei Tanaka" in answer
    cited_team = any(TEAM_URL in s for s in cited_sources)
    cited_only_team = cited_team and not any(LAUNCH_URL in s and TEAM_URL not in s
                                              for s in cited_sources)
    return {
        "ok": answer_correct and cited_team,
        "info": {
            "answer_preview": answer[:120],
            "cited_sources": cited_sources,
            "cited_team_url": cited_team,
            "cited_only_team": cited_only_team,
        },
        "error": None if (answer_correct and cited_team)
                 else "answer or citation source mismatch",
    }
