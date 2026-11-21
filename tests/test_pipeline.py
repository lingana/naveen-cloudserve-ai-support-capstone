from src.ingest import ingest_ticket
from src.classify import HeuristicClassifier
from src.route import Router
from src.guardrails import validate_answer


def test_all_channels_normalize():
    for channel in ("email", "chat", "docs_comment", "forum"):
        ticket = ingest_ticket({"ticket_id": "T1", "channel": channel, "body": "How do I reset access?"})
        assert ticket.channel == channel
        assert ticket.text


def test_classifier_has_required_fields():
    result = HeuristicClassifier().classify("The deployment is failing and I need a rollback")
    assert result["intent"] in {"deployment_failure", "rollback_request", "unclear_request"}
    assert result["urgency"] in {"low", "medium", "high"}
    assert 0 <= result["confidence"] <= 1


def test_same_route_is_deterministic():
    router = Router(0.80)
    classification = {"intent": "rate_limit", "confidence": 0.90, "urgency": "medium"}
    first = router.route(classification, [{"doc_id": "DOC-API-001"}])
    second = router.route(classification, [{"doc_id": "DOC-API-001"}])
    assert first == second


def test_security_ticket_always_escalates():
    router = Router(0.10)
    classification = {"intent": "security_incident", "confidence": 0.99, "urgency": "high"}
    action, reason = router.route(classification, [{"doc_id": "DOC-SEC-001"}], {})
    assert action == "escalate"


def test_private_data_guardrail_blocks():
    status, findings = validate_answer("Email me at person@example.com", [{"doc_id": "DOC-AUTH-001"}])
    assert status == "block"
    assert "private_data" in findings


def test_invented_citation_guardrail_blocks():
    status, findings = validate_answer("Follow the steps in DOC-FAKE-999.", [{"doc_id": "DOC-AUTH-001"}])
    assert status == "block"
    assert "invented_citation" in findings


def test_trained_classifier_runs_from_development_data():
    from pathlib import Path
    training = Path(__file__).resolve().parents[1] / "data" / "development_tickets.json"
    classifier = HeuristicClassifier(training_path=str(training))
    result = classifier.classify("I need help configuring single sign-on for my project")
    assert result["intent"]
    assert 0 <= result["confidence"] <= 1
    assert isinstance(result["alternatives"], list)
