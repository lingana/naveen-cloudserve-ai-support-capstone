import json
import os
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from .ingest import ingest_ticket
from .classify import HeuristicClassifier
from .retrieve import DocumentationRetriever
from .route import Router
from .generate import GroundedAnswerGenerator
from .guardrails import validate_answer
from .logging_store import DecisionStore

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _sources(passages):
    return [{"doc_id": p.doc_id, "title": p.title, "text": p.text[:500], "score": p.score} for p in passages]

class SupportPipeline:
    def __init__(self, data_path=None, db_path=None, confidence_threshold=None):
        data_path = data_path or os.path.join(BASE, "data", "documentation.json")
        db_path = db_path or os.getenv("DATABASE_URL", "sqlite:///./storage/decisions.db")
        threshold = confidence_threshold or float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
        retrieval_threshold = float(os.getenv("RETRIEVAL_THRESHOLD", "0.18"))
        training_path = os.path.join(BASE, "data", "development_tickets.json")
        model_path = os.path.join(BASE, "storage", "intent_classifier.joblib")
        self.classifier = HeuristicClassifier(
            training_path=training_path,
            model_path=model_path,
        )
        self.retriever = DocumentationRetriever(data_path, retrieval_threshold)
        self.router = Router(threshold)
        self.generator = GroundedAnswerGenerator()
        self.store = DecisionStore(db_path)

    def process(self, raw):
        started = time.perf_counter()
        ticket = ingest_ticket(raw)
        classification = self.classifier.classify(ticket.text)
        passages = self.retriever.retrieve(ticket.text)
        action, reason = self.router.route(classification, passages, ticket.labels)

        answer = None
        citations = []
        guardrails = []
        blocked = False
        if action == "answer":
            answer, citations, uncertainty = self.generator.generate(ticket, classification, passages)
            source_dicts = [{"doc_id": p.doc_id, "title": p.title, "text": p.text[:500], "score": p.score} for p in passages]
            guard_status, guardrails = validate_answer(answer, source_dicts)
            if guard_status == "block":
                action = "blocked"
                blocked = True
                reason = "Response blocked by guardrail: " + ", ".join(guardrails)
                answer = None
        else:
            uncertainty = "Escalated for human review"

        latency = time.perf_counter() - started
        result = {
            "ticket_id": ticket.ticket_id,
            "action": action,
            "intent": classification["intent"],
            "urgency": classification["urgency"],
            "confidence": classification["confidence"],
            "answer": answer,
            "citations": citations,
            "escalated": action == "escalate",
            "blocked": blocked,
            "reason": reason,
            "sources": _sources(passages),
            "guardrails": guardrails,
            "latency_seconds": latency,
        }
        now = datetime.now(timezone.utc).isoformat()
        self.store.add({
            "decision_id": str(uuid.uuid4()), "created_at": now,
            "ticket_id": ticket.ticket_id, "stage": "pipeline",
            "prediction": classification["intent"],
            "confidence": classification["confidence"], "threshold": self.router.threshold,
            "action_taken": action, "reason": reason,
            "sources_used": json.dumps([p.doc_id for p in passages]),
            "guardrails": json.dumps(guardrails), "prompt_version": "CLS-001:v1;GEN-001:v1;ESC-001:v1",
            "requirement_ids": "FR-01,FR-02,FR-03,FR-04,FR-05,FR-06,FR-07,FR-08,FR-09",
        })
        return result
