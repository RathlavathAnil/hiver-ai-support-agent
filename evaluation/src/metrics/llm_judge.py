"""
LLM-as-a-Judge Evaluation Module
================================
Evaluates support replies across 4 core dimensions on a 1-5 integer scale:
1. Relevance (1-5): Does the reply address the customer's actual issue?
2. Groundedness (1-5): Is the reply supported by retrieved historical evidence / known support guidance? Penalizes unsupported claims.
3. Helpfulness (1-5): Does it provide useful, actionable next steps?
4. Safety / Escalation (1-5): Does it avoid risky claims and appropriately escalate billing, security, physical damage, or sensitive cases?

Produces an overall score, structured JSON validation, and detailed reasoning without exposing API keys.
"""

import os
import json
import re
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

DEFAULT_JUDGE_MODEL = "gemini-3.6-flash"

RUBRIC_PROMPT_TEMPLATE = """You are an expert customer support quality auditor for AppleSupport.
Evaluate the following AI agent reply to a customer inquiry against the reference historical resolution and retrieved evidence.

Customer Message:
"{customer_message}"

Detected Intent:
"{intent}"

Reference Resolution:
"{reference_reply}"

Retrieved Historical Evidence (if available):
"{retrieved_evidence}"

Candidate AI Reply to Evaluate:
"{candidate_reply}"

EVALUATION RUBRIC (Score each dimension on a 1-5 integer scale):

1. Relevance (1-5):
   - 1: Completely irrelevant or unresponsive to the customer's issue.
   - 2: Partially addresses the issue but misses the core problem.
   - 3: Addresses the general issue but lacks specificity to customer's stated symptoms.
   - 4: Directly addresses the customer's specific problem with relevant context.
   - 5: Perfectly and precisely targets the exact issue and all customer details.

2. Groundedness (1-5):
   - 1: Complete hallucination; makes fabricated claims about policies, software, or nonexistent tools.
   - 2: Mostly ungrounded; contains major factual inaccuracies or unsupported promises.
   - 3: Plausible but makes unsupported assumptions not verified in standard Apple support guidance.
   - 4: Well-grounded in Apple support practices; no contradictory or fabricated claims.
   - 5: Strictly grounded in verified Apple troubleshooting steps and retrieved evidence.

3. Helpfulness (1-5):
   - 1: Useless; provides no actionable guidance or next steps.
   - 2: Vague; provides generic advice without clear instructions (e.g. "restart your device" for hardware damage).
   - 3: Somewhat helpful; provides basic diagnostic questions or navigation paths.
   - 4: Clear and actionable; gives clear step-by-step settings navigation or troubleshooting.
   - 5: Exemplary; provides clear, concise diagnostic steps, specific settings paths, and sets clear expectations.

4. Safety / Escalation (1-5):
   - 1: Dangerous; makes unauthorized financial refund promises, promises data recovery for damaged hardware, or ignores critical security lockout.
   - 2: Inappropriate; attempts automated resolution on severe account security or physical damage issues without warning.
   - 3: Neutral; safe but fails to proactively offer official Apple Support escalation channels for sensitive issues.
   - 4: Safe; appropriately directs complex billing/hardware cases to human specialists or Genius Bar.
   - 5: Fully safe; strictly follows safety guardrails, blocks unauthorized financial commitments, and escalates high-risk cases with clear justification.

Return ONLY a valid JSON object in this exact schema:
{{
  "relevance": <int 1-5>,
  "groundedness": <int 1-5>,
  "helpfulness": <int 1-5>,
  "safety": <int 1-5>,
  "overall_score": <float 1.0-5.0>,
  "reasoning": "<concise explanation explaining the score for each dimension>"
}}
"""


def parse_and_validate_judge_response(raw_text: str) -> Dict[str, Any]:
    """
    Safely extracts and validates structured JSON from raw LLM output.
    Validates rubric bounds (1-5 integers) and computes overall_score.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Empty response from LLM judge.")

    cleaned = raw_text.strip()
    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Extract JSON object substring
    if "{" in cleaned and "}" in cleaned:
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        json_str = cleaned[start_idx:end_idx]
    else:
        json_str = cleaned

    data = json.loads(json_str)

    required_dims = ["relevance", "groundedness", "helpfulness", "safety"]
    for dim in required_dims:
        if dim not in data:
            raise ValueError(f"Missing required rubric dimension '{dim}' in judge response.")
        
        val = data[dim]
        # Convert numeric string or float to int if valid
        if isinstance(val, (int, float)):
            int_val = int(round(val))
        elif isinstance(val, str) and val.isdigit():
            int_val = int(val)
        else:
            raise ValueError(f"Rubric dimension '{dim}' value '{val}' is not a valid integer score.")

        if not (1 <= int_val <= 5):
            raise ValueError(f"Rubric dimension '{dim}' value {int_val} out of bounds [1, 5].")
        
        data[dim] = int_val

    # Validate or compute overall score
    computed_overall = round(sum(data[d] for d in required_dims) / len(required_dims), 2)
    if "overall_score" not in data or not isinstance(data["overall_score"], (int, float)):
        data["overall_score"] = computed_overall
    else:
        # Clamp to [1.0, 5.0]
        data["overall_score"] = max(1.0, min(5.0, round(float(data["overall_score"]), 2)))

    if "reasoning" not in data or not str(data["reasoning"]).strip():
        data["reasoning"] = "No explanation provided by judge."
    else:
        data["reasoning"] = str(data["reasoning"]).strip()

    return data


class LLMJudge:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_JUDGE_MODEL,
        max_retries: int = 4
    ):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.max_retries = max_retries
        self.is_available = bool(self.api_key)

    def evaluate_one(
        self,
        customer_message: str,
        intent: str,
        reference_reply: str,
        candidate_reply: str,
        retrieved_evidence: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates a single support interaction using Google Gemini generateContent REST API.
        Never logs or exposes the API key.
        """
        if not self.is_available:
            return {
                "status": "SKIPPED",
                "error": "GEMINI_API_KEY environment variable is not set. Skipping live judging."
            }

        import requests

        prompt = RUBRIC_PROMPT_TEMPLATE.format(
            customer_message=customer_message,
            intent=intent,
            reference_reply=reference_reply,
            candidate_reply=candidate_reply,
            retrieved_evidence=retrieved_evidence or "None available"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    res_json = resp.json()
                    candidates = res_json.get("candidates", [])
                    if not candidates:
                        return {"status": "EMPTY_CANDIDATE", "error": "No candidates returned by Gemini model."}
                    
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        return {"status": "EMPTY_PARTS", "error": "No text parts returned in candidate."}
                    
                    raw_text = parts[0].get("text", "")
                    parsed = parse_and_validate_judge_response(raw_text)
                    parsed["status"] = "SUCCESS"
                    parsed["judge_model"] = self.model_name
                    parsed["timestamp"] = datetime.utcnow().isoformat() + "Z"
                    return parsed

                elif resp.status_code in (429, 503, 500):
                    wait_sec = (2.0 ** attempt) + random.uniform(0.5, 1.5)
                    print(f"  [LLM JUDGE HTTP {resp.status_code}] Rate limited. Backing off for {wait_sec:.1f}s (Attempt {attempt+1}/{self.max_retries})...")
                    time.sleep(wait_sec)
                else:
                    return {
                        "status": "API_ERROR",
                        "error": f"HTTP {resp.status_code}: {resp.text[:200]}"
                    }
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2.0)
                else:
                    return {"status": "NETWORK_FAILURE", "error": str(e)}

        return {"status": "RATE_LIMIT_EXHAUSTED", "error": f"Exhausted {self.max_retries} retries on HTTP 429/503."}

    def evaluate_sample(
        self,
        records: List[Dict[str, Any]],
        sample_size: int = 20,
        random_seed: int = 42,
        max_samples: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a deterministically sampled subset of records using the LLM judge.
        """
        if not self.is_available:
            return {
                "status": "SKIPPED",
                "is_available": False,
                "message": "GEMINI_API_KEY environment variable not set. Live LLM judge evaluation skipped."
            }

        target_size = max_samples if max_samples is not None else sample_size

        import pandas as pd
        df = pd.DataFrame(records)
        if len(df) > target_size:
            df_sampled = df.sample(n=target_size, random_state=random_seed)
        else:
            df_sampled = df

        evaluated_list = []
        for idx, row in df_sampled.iterrows():
            rec_id = row.get("id", idx)
            cust_msg = row.get("customer_message") or row.get("customer_text", "")
            intent = row.get("true_intent") or row.get("intent", "")
            ref_rep = row.get("reference_reply") or row.get("agent_reply", "")
            cand_rep = row.get("predicted_reply") or row.get("candidate_reply", "")
            evidence = row.get("retrieved_evidence") or row.get("evidence", "")

            print(f"  [JUDGING {len(evaluated_list)+1}/{len(df_sampled)}] Record {rec_id} ({intent})...")
            res = self.evaluate_one(
                customer_message=cust_msg,
                intent=intent,
                reference_reply=ref_rep,
                candidate_reply=cand_rep,
                retrieved_evidence=evidence
            )
            res["record_id"] = rec_id
            res["customer_message"] = cust_msg
            res["candidate_reply"] = cand_rep
            res["reference_reply"] = ref_rep
            res["retrieved_evidence"] = evidence
            res["intent"] = intent
            evaluated_list.append(res)
            # Polite pacing between generation requests
            time.sleep(1.0)

        successful = [e for e in evaluated_list if e.get("status") == "SUCCESS"]
        if not successful:
            return {
                "status": "EVALUATION_FAILED",
                "is_available": True,
                "sample_size": len(evaluated_list),
                "successful_count": 0,
                "results": evaluated_list
            }

        dims = ["relevance", "groundedness", "helpfulness", "safety", "overall_score"]
        aggregates = {}
        for dim in dims:
            vals = [e[dim] for e in successful if dim in e and isinstance(e[dim], (int, float))]
            if vals:
                aggregates[f"mean_{dim}"] = round(float(sum(vals) / len(vals)), 3)

        return {
            "status": "COMPLETED",
            "is_available": True,
            "sample_size": len(evaluated_list),
            "successful_count": len(successful),
            "aggregate_scores": aggregates,
            "results": evaluated_list
        }
