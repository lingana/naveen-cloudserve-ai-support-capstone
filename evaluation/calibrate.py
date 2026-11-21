import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]


def calibration_table(y_true, confidences, bands=5):
    rows = []
    for band in range(bands):
        low = band / bands
        high = (band + 1) / bands
        indices = [i for i, confidence in enumerate(confidences) if low <= confidence < high]
        if not indices:
            continue
        stated = sum(confidences[i] for i in indices) / len(indices)
        observed = sum(y_true[i] for i in indices) / len(indices)
        rows.append({
            "band": f"{low:.2f}-{high:.2f}",
            "count": len(indices),
            "stated_confidence": round(stated, 4),
            "observed_accuracy": round(observed, 4),
            "calibration_error": round(stated - observed, 4),
        })
    return rows


def run():
    tickets = json.loads((ROOT / "data" / "development_tickets.json").read_text(encoding="utf-8"))
    texts = [f"{ticket.get('subject', '')}\n{ticket.get('body', '')}" for ticket in tickets]
    intents = [ticket["labels"]["intent"] for ticket in tickets]

    x_train, x_test, y_train, y_test = train_test_split(texts, intents, test_size=0.25, random_state=42, stratify=intents)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=30000)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)
    predicted = model.predict(x_test)
    confidences = probabilities.max(axis=1).tolist()
    correct = [predicted[i] == y_test[i] for i in range(len(y_test))]

    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    routing = []
    for threshold in thresholds:
        answered = sum(confidence >= threshold for confidence in confidences)
        correctly_answered = sum(confidence >= threshold and correct[i] for i, confidence in enumerate(confidences))
        routing.append({
            "threshold": threshold,
            "answered": answered,
            "answered_correctly": correctly_answered,
            "answer_precision": round(correctly_answered / answered, 4) if answered else 0.0,
            "escalated": len(confidences) - answered,
        })

    report = {
        "sample": "development held-out split",
        "development_tickets": len(tickets),
        "test_tickets": len(y_test),
        "overall_accuracy": round(sum(correct) / len(correct), 4),
        "calibration": calibration_table(correct, confidences),
        "routing_thresholds": routing,
        "note": "Thresholds are for development holdout analysis only; validation and hidden sets must not be used to tune the classifier repeatedly.",
    }
    output = ROOT / "evaluation" / "results" / "calibration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
