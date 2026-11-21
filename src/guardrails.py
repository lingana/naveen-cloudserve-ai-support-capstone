import re

PRIVATE_PATTERNS = [
    re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'),
    re.compile(r'(?i)\b(?:api[_-]?key|token|password)\s*[:=]\s*[^\s,;]+'),
]

def validate_answer(answer: str, sources: list) -> tuple[str, list]:
    findings = []
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(answer):
            findings.append("private_data")
            break
    injected = re.search(r"(?i)ignore\s+(?:all|previous|your)\s+instructions|reveal\s+(?:your|the)\s+prompt", answer)
    if injected:
        findings.append("prompt_injection")
    prohibited = re.compile(r"(?i)refund has been issued|refund issued|guaranteed|password\s+is\s+", re.I)
    if prohibited.search(answer):
        findings.append("unsupported_commitment")
    source_ids = {s["doc_id"] for s in sources}
    citation_ids = set(re.findall(r"DOC-[A-Z0-9-]+", answer))
    if citation_ids - source_ids:
        findings.append("invented_citation")
    if findings:
        return "block", list(dict.fromkeys(findings))
    return "pass", []
