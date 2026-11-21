from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

@dataclass
class NormalizedTicket:
    ticket_id: str
    channel: str
    subject: str
    body: str
    customer_id: str = ""
    customer_name: str = ""
    customer_tier: str = ""
    customer_region: str = ""
    language_fluency: str = ""
    labels: Dict[str, Any] = field(default_factory=dict)
    history: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self):
        return f"{self.subject}\n{self.body}".strip()

@dataclass
class Passage:
    doc_id: str
    title: str
    text: str
    score: float

    def to_dict(self):
        return asdict(self)

@dataclass
class PipelineResult:
    ticket_id: str
    action: str
    intent: str
    urgency: str
    confidence: float
    answer: Optional[str]
    citations: List[Dict[str, Any]]
    escalated: bool
    blocked: bool
    reason: str
    sources: List[Dict[str, Any]]
    guardrails: List[str]

    def to_dict(self):
        return asdict(self)
