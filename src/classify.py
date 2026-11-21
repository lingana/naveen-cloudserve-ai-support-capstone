from pathlib import Path
import json

from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

INTENTS = [
"account_access","api_key_issue","api_usage_question","authentication_failure","billing_query",
"compliance_request","configuration_help","data_export","data_residency","database_issue",
"deployment_failure","feature_request","integration_help","onboarding","performance_degradation",
"quota_or_overage","rate_limit","rollback_request","security_incident","sso_configuration",
"unclear_request","webhook_issue"]

KEYWORDS = {
"security_incident":["breach","compromise","leak","unauthorized","malware"],
"data_residency":["gdpr","eu","data location","region","residency","privacy"],
"billing_query":["invoice","charge","refund","billing","cost","price"],
"authentication_failure":["login","log in","password","credential","sign in"],
"deployment_failure":["deployment","pipeline","build","container","deploy"],
"rollback_request":["rollback","revert","previous revision","undo"],
"rate_limit":["rate limit","429","throttle"],
"api_key_issue":["api key","apikey","invalid key","key"],
"api_usage_question":["pagination","api","endpoint","sdk","cursor"],
"data_export":["export","csv","download","records"],
"database_issue":["database","restore","postgres","mysql","query"],
"sso_configuration":["single sign-on","saml","sso","oidc"],
"quota_or_overage":["quota","overage","allowance","limit","cap"],
"performance_degradation":["slow","latency","timeout","performance","degradation"],
"account_access":["access","permission","locked","project member"],
"webhook_issue":["webhook","callback","event delivery"],
"integration_help":["ci pipeline","github","gitlab","integration","connecting"],
"compliance_request":["compliance","audit","certification","soc"],
"feature_request":["please add","feature","wish","roadmap"],
"onboarding":["getting started","onboard","new project","setup"],
"configuration_help":["configure","configuration","setting","misconfigured"],
}

class HeuristicClassifier:
    def __init__(self, training_path: str = None, model_path: str = None):
        self.training = []
        self.model = None
        if training_path and Path(training_path).exists():
            self.training = json.loads(Path(training_path).read_text(encoding="utf-8"))
            self.train()
        elif model_path and Path(model_path).exists():
            self.model = load(model_path)

    def train(self):
        texts = [f"{row.get('subject', '')}\n{row.get('body', '')}" for row in self.training]
        labels = [row["labels"]["intent"] for row in self.training]
        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=30000)),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        self.model.fit(texts, labels)

    def save(self, path: str):
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        dump(self.model, destination)

    def classify(self, text: str):
        text_lower = text.lower()
        ml_intent = None
        ml_confidence = 0.0
        alternatives = []
        if self.model is not None:
            ml_intent = str(self.model.predict([text])[0])
            probabilities = self.model.predict_proba([text])[0]
            classes = list(self.model.classes_)
            ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
            ml_confidence = float(ranked[0][1])
            alternatives = [{"intent": intent, "confidence": float(probability)} for intent, probability in ranked[1:4]]

        scores = {intent: 0.0 for intent in INTENTS}
        for intent, words in KEYWORDS.items():
            scores[intent] = sum(1.0 for word in words if word in text_lower)
        heuristic_intent = max(scores, key=scores.get)
        heuristic_score = scores[heuristic_intent]

        if ml_intent:
            intent = ml_intent
            confidence = ml_confidence
        else:
            intent = heuristic_intent if heuristic_score > 0 else "unclear_request"
            confidence = min(0.95, 0.55 + 0.10 * heuristic_score) if heuristic_score > 0 else 0.35

        if not alternatives:
            alternatives = [{"intent": i, "confidence": min(0.95, 0.50 + 0.10 * score)}
                            for i, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                            if i != intent]

        urgency = (
            "high" if any(word in text_lower for word in ["down", "outage", "breach", "critical", "cannot ship", "failing", "production"])
            else "medium" if any(word in text_lower for word in ["slow", "error", "issue", "broken", "deadline"])
            else "low"
        )
        return {"intent": intent, "urgency": urgency, "confidence": confidence,
                "alternatives": alternatives, "missing_information": []}
