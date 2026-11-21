import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import SupportPipeline


def run(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    tickets = json.loads(input_path.read_text(encoding="utf-8"))
    documentation_path = ROOT / "data" / "documentation.json"
    pipeline = SupportPipeline(data_path=str(documentation_path))

    results = []
    latencies = []
    for ticket in tickets:
        try:
            result = pipeline.process(ticket)
        except Exception as exc:
            result = {
                "ticket_id": ticket.get("ticket_id", "UNKNOWN"), "action": "escalate",
                "intent": "unclear_request", "urgency": "high", "confidence": 0.0,
                "answer": None, "citations": [], "escalated": True, "blocked": False,
                "reason": f"Controlled failure: {type(exc).__name__}", "sources": [],
                "guardrails": [], "latency_seconds": 0.0,
            }
        results.append(result)
        latencies.append(float(result.get("latency_seconds", 0.0)))

    actions = Counter(r["action"] for r in results)
    escalated = sum(r["escalated"] for r in results)
    blocked = sum(r["blocked"] for r in results)

    intent_by_truth = defaultdict(list)
    for ticket, result in zip(tickets, results):
        truth = ticket.get("labels", {}).get("intent")
        if truth:
            intent_by_truth[truth].append(result["intent"] == truth)

    classification = {}
    for intent, checks in sorted(intent_by_truth.items(),
                                  key=lambda item: sum(item[1]), reverse=True):
        tp = sum(checks)
        predicted = sum(1 for r in results if r["intent"] == intent)
        actual = len(checks)
        classification[intent] = {
            "precision": round(tp / predicted, 4) if predicted else 0.0,
            "recall": round(tp / actual, 4) if actual else 0.0,
        }

    sorted_latency = sorted(latencies)
    p95 = sorted_latency[min(len(sorted_latency)-1, int(0.95 * len(sorted_latency)))] if sorted_latency else 0.0

    calibration_path = ROOT / "evaluation" / "results" / "calibration.json"
    calibration_status = "not_run"
    if calibration_path.exists():
        calibration_status = "held-out development calibration report available"

    metrics = {
        "volume": {"tickets_processed": len(results), "answered": actions.get("answer", 0),
                   "escalated": escalated, "blocked": blocked},
        "business": {"escalation_rate": round(escalated / len(results), 4) if results else 0.0,
                     "first_contact_resolution_proxy": round(actions.get("answer", 0) / len(results), 4) if results else 0.0,
                     "mean_response_time_seconds": round(statistics.mean(latencies), 4) if latencies else 0.0,
                     "median_response_time_seconds": round(statistics.median(latencies), 4) if latencies else 0.0},
        "technical": {"classification": classification,
                      "latency_median_seconds": round(statistics.median(latencies), 4) if latencies else 0.0,
                      "latency_p95_seconds": round(p95, 4),
                      "retrieval_hits": sum(bool(r["sources"]) for r in results),
                      "retrieval_hit_rate": round(sum(bool(r["sources"]) for r in results) / len(results), 4) if results else 0.0},
        "governance": {"decision_log_records": pipeline.store.count(),
                       "guardrail_activations": dict(Counter(g for r in results for g in r["guardrails"])),
                       "private_data_detections": sum("private_data" in r["guardrails"] for r in results),
                       "confidence_calibration": calibration_status,
                       "hidden_set_evaluated": False,
                       "human_citation_review_completed": False,
                       "human_hallucination_review_completed": False,
                       "minimum_human_review_samples": 50,
                       "minimum_independent_assessors": 2},
        "calibration": {"status": calibration_status},
    }

    (output_path / "ticket_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output_path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.input, args.output)
