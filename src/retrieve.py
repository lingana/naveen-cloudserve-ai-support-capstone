import json
import re
from pathlib import Path

from .models import Passage

STOP_WORDS = {"the", "a", "an", "is", "to", "of", "in", "on", "for", "and", "or", "with", "my", "i", "our", "we", "it", "this", "that", "how", "why", "from"}


def tokens(text: str):
    return {term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 2 and term not in STOP_WORDS}


class DocumentationRetriever:
    def __init__(self, documentation_path: str, threshold: float = 0.12):
        path = Path(documentation_path)
        self.docs = json.loads(path.read_text(encoding="utf-8"))
        self.threshold = threshold

    def retrieve(self, text: str, top_k: int = 5):
        query_tokens = tokens(text)
        ranked = []
        for doc in self.docs:
            applies_to = doc.get("applies_to", "")
            if isinstance(applies_to, list):
                applies_to = " ".join(applies_to)
            title_tokens = tokens(doc.get("title", ""))
            category_tokens = tokens(doc.get("category", "") + " " + str(applies_to))
            content_tokens = tokens(doc.get("content", ""))
            title_overlap = len(query_tokens.intersection(title_tokens))
            content_overlap = len(query_tokens.intersection(content_tokens))
            category_overlap = len(query_tokens.intersection(category_tokens))
            union = query_tokens.union(content_tokens)
            jaccard = len(query_tokens.intersection(content_tokens)) / max(1, len(union))
            score = (
                0.55 * content_overlap / max(1, len(query_tokens))
                + 0.30 * jaccard
                + 0.15 * title_overlap / max(1, len(query_tokens))
                + 0.10 * category_overlap
            )
            ranked.append(Passage(
                doc_id=doc["doc_id"],
                title=doc["title"],
                text=doc["content"],
                score=min(1.0, score),
            ))
        ranked.sort(key=lambda x: x.score, reverse=True)
        return [passage for passage in ranked[:top_k] if passage.score >= self.threshold]
