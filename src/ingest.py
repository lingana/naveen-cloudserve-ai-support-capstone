from .models import NormalizedTicket

CHANNELS = {"email", "chat", "docs_comment", "forum"}

def ingest_ticket(raw: dict) -> NormalizedTicket:
    if not isinstance(raw, dict):
        raise ValueError("Ticket must be a JSON object")
    channel = str(raw.get("channel", "unknown")).strip().lower()
    if channel not in CHANNELS:
        raise ValueError(f"Unsupported channel: {channel}")
    body = raw.get("body")
    if body is None:
        body = ""
    if not isinstance(body, str):
        raise ValueError("Ticket body must be text")
    return NormalizedTicket(
        ticket_id=str(raw.get("ticket_id", "UNKNOWN")), channel=channel,
        subject=str(raw.get("subject", "") or ""), body=body,
        customer_id=str(raw.get("customer_id", "") or ""),
        customer_name=str(raw.get("customer_name", "") or ""),
        customer_tier=str(raw.get("customer_tier", "") or ""),
        customer_region=str(raw.get("customer_region", "") or ""),
        language_fluency=str(raw.get("language_fluency", "") or ""),
        labels=raw.get("labels", {}) if isinstance(raw.get("labels", {}), dict) else {},
        history=raw.get("history", {}) if isinstance(raw.get("history", {}), dict) else {},
    )
