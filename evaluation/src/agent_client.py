"""
Spring Boot Agent REST API Client
=================================
Calls the live Spring Boot AI Support Agent REST API endpoint (POST /api/v1/support)
and formats responses for evaluation against the golden evaluation set.
"""

import time
import requests
from typing import Dict, List, Any, Optional


class AgentClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/api/v1/support"
        self.health_url = f"{self.base_url}/api/v1/support/health"
        self.timeout = timeout

    def check_health(self) -> bool:
        """Checks if the Spring Boot application is healthy and responsive."""
        try:
            resp = requests.get(self.health_url, timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def predict_one(self, customer_message: str) -> Dict[str, Any]:
        """Sends a single support inquiry to the Spring Boot REST endpoint."""
        payload = {"message": customer_message}
        try:
            start_t = time.time()
            resp = requests.post(self.endpoint, json=payload, timeout=self.timeout)
            latency_ms = (time.time() - start_t) * 1000

            if resp.status_code == 200:
                data = resp.json()
                esc = data.get("escalation", {})
                return {
                    "predicted_intent": data.get("intent", "GENERAL_PRODUCT_INQUIRY"),
                    "confidence": float(data.get("confidence", 0.0)),
                    "predicted_reply": data.get("reply", ""),
                    "predicted_decision": esc.get("decision", "AUTO_HANDLE"),
                    "predicted_escalation_reason": esc.get("reason", ""),
                    "similar_conversations": data.get("similarConversations", []),
                    "latency_ms": latency_ms,
                    "status": "SUCCESS"
                }
            else:
                return {
                    "status": "HTTP_ERROR",
                    "status_code": resp.status_code,
                    "error": resp.text,
                    "predicted_intent": "GENERAL_PRODUCT_INQUIRY",
                    "confidence": 0.0,
                    "predicted_reply": "Support service temporarily unavailable.",
                    "predicted_decision": "ESCALATE",
                    "predicted_escalation_reason": f"API error HTTP {resp.status_code}"
                }
        except Exception as e:
            return {
                "status": "CONNECTION_ERROR",
                "error": str(e),
                "predicted_intent": "GENERAL_PRODUCT_INQUIRY",
                "confidence": 0.0,
                "predicted_reply": "Connection to support agent failed.",
                "predicted_decision": "ESCALATE",
                "predicted_escalation_reason": f"Connection error: {str(e)}"
            }

    def evaluate_dataset(self, test_df) -> List[Dict[str, Any]]:
        """Evaluates the Spring Boot agent across all test records."""
        results = []
        for _, row in test_df.iterrows():
            msg = str(row.get("customer_message", ""))
            pred = self.predict_one(msg)
            pred["id"] = row.get("id")
            pred["conversation_id"] = row.get("conversation_id")
            pred["customer_message"] = msg
            pred["true_intent"] = row.get("intent")
            pred["true_decision"] = row.get("expected_decision")
            pred["reference_reply"] = row.get("reference_reply")
            pred["difficulty"] = row.get("difficulty")
            results.append(pred)
        return results
