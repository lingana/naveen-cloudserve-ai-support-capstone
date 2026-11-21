import re


def citation_accuracy(citations, passages):
    """Measure whether every generated citation resolves to a retrieved passage.

    This is an automated citation-resolution metric, not a human semantic-support score.
    """
    allowed = {passage.doc_id for passage in passages}
    if not citations:
        return 0.0, 0
    resolved = sum(1 for citation in citations if citation.get("doc_id") in allowed)
    return resolved / len(citations), len(citations)


def unsupported_claim_markers(answer: str):
    """Return simple prohibited/unsupported markers for automated review."""
    markers = []
    patterns = {
        "refund_commitment": r"(?i)refund has been issued|refund will be issued|we guarantee a refund",
        "security_claim": r"(?i)account is definitely compromised|breach is confirmed|security issue is confirmed",
        "invented_citation": r"(?i)\bDOC-[A-Z0-9-]+\b",
        "private_data": r"(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|api[_-]?key\s*[:=]",
    }
    for name, pattern in patterns.items():
        if re.search(pattern, answer):
            if name == "invented_citation":
                continue
            markers.append(name)
    return markers


def estimate_hallucination(answer: str, citations, passages):
    """Automated conservative estimate; final hallucination rate needs human review."""
    if not answer:
        return None
    citation_ratio, _ = citation_accuracy(citations, passages)
    markers = unsupported_claim_markers(answer)
    suspicious = bool(markers) or citation_ratio < 1.0
    return {
        "automated_suspicious": suspicious,
        "markers": markers,
        "citation_resolution_ratio": citation_ratio,
        "human_review_required": True,
    }
