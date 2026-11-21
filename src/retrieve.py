import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Passage


def split_markdown_passages(content: str, doc_id: str, chunk_size: int = 900):
    """Split an article by paragraphs while keeping chunks below the target size."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\n(?=#{1,6}\s)|\n(?=-\s)", content) if p.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > chunk_size:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


class DocumentationRetriever:
    def __init__(self, documentation_path: str, threshold: float = 0.05):
        path = Path(documentation_path)
        self.docs = json.loads(path.read_text(encoding="utf-8"))
        self.threshold = threshold
        self.chunks = []
        for doc in self.docs:
            for index, chunk in enumerate(split_markdown_passages(doc.get("content", ""), doc["doc_id"])):
                self.chunks.append({
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "text": chunk,
                    "chunk_id": f"{doc['doc_id']}:{index + 1}",
                })

        texts = [f"{chunk['title']} {chunk['text']}" for chunk in self.chunks]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None

    def retrieve(self, text: str, top_k: int = 5):
        if not text or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([text])
        similarities = cosine_similarity(query_vector, self.matrix)[0]
        query_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
        scored_indices = []
        for index, similarity in enumerate(similarities):
            chunk = self.chunks[index]
            title_tokens = set(re.findall(r"[a-z0-9]+", chunk["title"].lower()))
            title_overlap = len(query_tokens.intersection(title_tokens))
            boosted = float(similarity) + 0.03 * min(title_overlap, 3)
            scored_indices.append((boosted, index))
        scored_indices.sort(reverse=True)
        ranked_indices = [index for _, index in scored_indices[:top_k]]
        ranked = []
        for index in ranked_indices:
            score = float(similarities[index])
            if score >= self.threshold:
                chunk = self.chunks[index]
                ranked.append(Passage(
                    doc_id=chunk["doc_id"],
                    title=chunk["title"],
                    text=chunk["text"],
                    score=score,
                ))
        return ranked
