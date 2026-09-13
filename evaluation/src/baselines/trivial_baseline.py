"""
Trivial / Majority Baseline Classifier & Response System
=========================================================
1. Intent: Predicts the majority class computed from non-golden training data.
2. Reply: Returns the most frequent historical brand troubleshooting template.
3. Escalation: Always predicts AUTO_HANDLE.
"""

import pandas as pd
from typing import Dict, List, Any


class TrivialBaseline:
    def __init__(self):
        self.majority_intent = "GENERAL_PRODUCT_INQUIRY"
        self.default_reply = "We're here to help! Please send us a DM with your device model and iOS version: https://support.apple.com"
        self.default_decision = "AUTO_HANDLE"
        self.default_reason = "Standard automated support inquiry resolvable via troubleshooting documentation."

    def fit(self, train_df: pd.DataFrame):
        """Fits majority class on training data (excluding golden set)."""
        if "intent" in train_df.columns and not train_df["intent"].dropna().empty:
            self.majority_intent = train_df["intent"].mode()[0]
        return self

    def predict_one(self, customer_message: str) -> Dict[str, Any]:
        return {
            "predicted_intent": self.majority_intent,
            "confidence": 1.0,
            "predicted_reply": self.default_reply,
            "predicted_decision": self.default_decision,
            "predicted_escalation_reason": self.default_reason
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
