"""
Simple ML Baseline: TF-IDF + Logistic Regression
=================================================
1. Intent: TF-IDF (unigram + bigram) + Logistic Regression trained on non-golden AppleSupport pairs.
2. Reply: TF-IDF Cosine Similarity retrieval of closest historical brand reply.
3. Escalation: Rule-based keyword matching + confidence thresholding.
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity


class MLBaseline:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            stop_words="english"
        )
        self.classifier = LogisticRegression(
            C=1.0,
            max_iter=500,
            random_state=random_state
        )
        self.reply_vectorizer = TfidfVectorizer(max_features=3000, stop_words="english")
        self.historical_replies: List[str] = []
        self.historical_reply_matrix = None
        self.is_fitted = False
        self.escalation_keywords = [
            "cancel", "legal", "lawyer", "manager", "supervisor", "refund",
            "complaint", "sue", "fraud", "hacked", "stolen", "unauthorized",
            "crack", "water damage", "liquid"
        ]

    def fit(self, train_df: pd.DataFrame):
        """Fits TF-IDF and Logistic Regression on non-golden training pairs."""
        clean_df = train_df.dropna(subset=["customer_text", "intent"]).copy()
        texts = clean_df["customer_text"].tolist()
        labels = clean_df["intent"].tolist()

        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)

        # Index historical replies for TF-IDF retrieval
        if "agent_reply" in clean_df.columns:
            reply_df = clean_df.dropna(subset=["agent_reply"]).drop_duplicates(subset=["customer_text"])
            self.historical_replies = reply_df["agent_reply"].tolist()
            self.historical_reply_matrix = self.reply_vectorizer.fit_transform(reply_df["customer_text"].tolist())

        self.is_fitted = True
        return self

    def predict_one(self, customer_message: str) -> Dict[str, Any]:
        if not self.is_fitted:
            raise RuntimeError("MLBaseline must be fitted before calling predict.")

        # 1. Intent Classification
        X_vec = self.vectorizer.transform([customer_message])
        probs = self.classifier.predict_proba(X_vec)[0]
        max_idx = np.argmax(probs)
        pred_intent = self.classifier.classes_[max_idx]
        confidence = float(probs[max_idx])

        # 2. Reply Retrieval via TF-IDF Cosine Similarity
        pred_reply = "We're here to help! Please send us a DM with your device model and iOS version: https://support.apple.com"
        if self.historical_reply_matrix is not None and len(self.historical_replies) > 0:
            query_vec = self.reply_vectorizer.transform([customer_message])
            sims = cosine_similarity(query_vec, self.historical_reply_matrix)[0]
            top_reply_idx = int(np.argmax(sims))
            if sims[top_reply_idx] > 0.15:
                pred_reply = self.historical_replies[top_reply_idx]

        # 3. Keyword + Confidence Escalation Rules
        lower_msg = customer_message.lower()
        decision = "AUTO_HANDLE"
        reason = "Standard automated support inquiry resolvable via troubleshooting documentation."

        for kw in self.escalation_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower_msg):
                decision = "ESCALATE"
                reason = f"Triggered high-risk keyword guardrail: '{kw}'"
                break

        if decision == "AUTO_HANDLE" and confidence < 0.55:
            decision = "ESCALATE"
            reason = f"ML confidence ({confidence:.2f}) below threshold 0.55"
        elif decision == "AUTO_HANDLE" and pred_intent in ["HARDWARE_PHYSICAL_DAMAGE", "ACCOUNT_ACCESS_SECURITY", "BILLING_SUBSCRIPTIONS"]:
            decision = "ESCALATE"
            reason = f"High-risk intent policy: {pred_intent}"

        return {
            "predicted_intent": pred_intent,
            "confidence": confidence,
            "predicted_reply": pred_reply,
            "predicted_decision": decision,
            "predicted_escalation_reason": reason
        }

    def evaluate_dataset(self, test_df: pd.DataFrame) -> List[Dict[str, Any]]:
        results = []
        for _, row in test_df.iterrows():
            pred = self.predict_one(str(row.get("customer_message", "")))
            pred["id"] = row.get("id")
            pred["conversation_id"] = row.get("conversation_id")
            pred["customer_message"] = row.get("customer_message")
            pred["true_intent"] = row.get("intent")
            pred["true_decision"] = row.get("expected_decision")
            pred["reference_reply"] = row.get("reference_reply")
            pred["difficulty"] = row.get("difficulty")
            results.append(pred)
        return results
