from dataclasses import asdict

HARD_ESCALATE = {"security_incident", "compliance_request", "feature_request", "unclear_request", "data_residency", "billing_query"}

class Router:
    def __init__(self, threshold: float = 0.30):
        self.threshold = threshold

    def route(self, classification: dict, passages: list, ticket_labels: dict = None):
        intent = classification["intent"]
        confidence = float(classification["confidence"])
        if ticket_labels and ticket_labels.get("must_not_auto_respond"):
            return "escalate", "Ticket is marked must-not-auto-respond"
        if intent in HARD_ESCALATE:
            return "escalate", f"Intent {intent} requires human handling"
        if not passages:
            return "escalate", "No relevant documentation passage was retrieved"
        if confidence < self.threshold:
            return "escalate", f"Confidence {confidence:.2f} is below threshold {self.threshold:.2f}"
        return "answer", f"Confidence {confidence:.2f} meets threshold and relevant documentation was retrieved"
