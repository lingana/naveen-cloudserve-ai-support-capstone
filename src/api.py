from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from .pipeline import SupportPipeline

app = FastAPI(title="CloudServe Support Pipeline")
pipeline = None

class Ticket(BaseModel):
    ticket_id: str
    channel: str
    subject: str = ""
    body: str = ""
    customer_id: str = ""
    customer_name: str = ""
    customer_tier: str = ""
    customer_region: str = ""
    language_fluency: str = ""
    labels: Dict[str, Any] = {}
    history: Dict[str, Any] = {}

@app.on_event("startup")
def startup():
    global pipeline
    pipeline = SupportPipeline()

@app.get("/health")
def health():
    return {"status": "ok", "decision_log_records": pipeline.store.count() if pipeline else 0}

@app.post("/process")
def process(ticket: Ticket):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    try:
        return pipeline.process(ticket.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
