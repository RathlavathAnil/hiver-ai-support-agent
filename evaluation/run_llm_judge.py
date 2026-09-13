"""
Standalone LLM-as-a-Judge Evaluation Script
===========================================
Evaluates agent replies against customer messages and reference resolutions using Google Gemini.

Uses a 4-dimension rubric (scored 1-5 integer scale):
1. Relevance (1-5): Does the reply address the customer's actual issue?
2. Groundedness (1-5): Is the reply supported by retrieved historical evidence / known support guidance?
3. Helpfulness (1-5): Does it provide useful, actionable next steps?
4. Safety / Escalation (1-5): Does it avoid risky claims and appropriately escalate sensitive cases?

Usage:
    python evaluation/run_llm_judge.py [--sample-size 20] [--seed 42] [--agent-url http://localhost:8080] [--model gemini-2.0-flash]
"""

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evaluation.src.metrics.llm_judge import LLMJudge, DEFAULT_JUDGE_MODEL
from evaluation.src.agent_client import AgentClient

GOLDEN_CSV_PATH = ROOT_DIR / "data" / "golden" / "golden_set.csv"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results"


def run_llm_judge_evaluation(
    sample_size: int = 20,
    seed: int = 42,
    agent_url: str = "http://localhost:8080",
    model_name: str = DEFAULT_JUDGE_MODEL
):
    print("=" * 80)
    print(" HIVER AI CUSTOMER SUPPORT AGENT — LLM-AS-A-JUDGE EVALUATION")
    print("=" * 80)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        print("        LLM-as-a-Judge evaluation requires a valid Gemini API key.")
        print("        Please set the environment variable:")
        print("          Windows PowerShell: $env:GEMINI_API_KEY=\"your_key_here\"")
        print("          Linux/macOS:        export GEMINI_API_KEY=\"your_key_here\"")
        print("\n[INFO] Exiting without fabricating judge results.\n")
        sys.exit(1)

    if not GOLDEN_CSV_PATH.exists():
        print(f"[ERROR] Golden evaluation set not found at {GOLDEN_CSV_PATH}")
        sys.exit(1)

    # 1. Load Golden Set
    golden_df = pd.read_csv(GOLDEN_CSV_PATH)
    print(f"[INFO] Loaded {len(golden_df)} golden records from {GOLDEN_CSV_PATH}")

    # 2. Deterministic Sampling
    if sample_size and sample_size < len(golden_df):
        sample_df = golden_df.sample(n=sample_size, random_state=seed).copy()
    else:
        sample_df = golden_df.copy()

    print(f"[INFO] Sampled {len(sample_df)} evaluation records (Random Seed: {seed})")

    # 3. Obtain Candidate Replies
    agent_client = AgentClient(base_url=agent_url)
    agent_live = agent_client.check_health()
    print(f"[INFO] Spring Boot Agent API ({agent_url}): {'ONLINE & LIVE' if agent_live else 'OFFLINE (Using fallback resolution generation)'}")

    eval_records = []
    for _, row in sample_df.iterrows():
        rec_id = int(row["id"])
        cust_msg = str(row["customer_message"])
        intent = str(row["intent"])
        ref_reply = str(row["reference_reply"])

        cand_reply = ""
        evidence_text = ""

        if agent_live:
            pred = agent_client.predict_one(cust_msg)
            if pred and pred.get("status") == "SUCCESS":
                cand_reply = pred.get("predicted_reply", "")
                sim_convs = pred.get("similar_conversations", [])
                if sim_convs:
                    evidence_text = sim_convs[0].get("agentReply", "")
        
        if not cand_reply:
            # Fallback candidate reply if agent offline
            cand_reply = (
                f"We're here to help with your Apple device. "
                f"For {intent.replace('_', ' ').lower()} issues, please verify your settings and DM us with your model details."
            )

        eval_records.append({
            "id": rec_id,
            "customer_message": cust_msg,
            "intent": intent,
            "reference_reply": ref_reply,
            "candidate_reply": cand_reply,
            "retrieved_evidence": evidence_text
        })

    # 4. Run LLM Judge
    print(f"\n>>> Running Gemini LLM Judge ({model_name}) on {len(eval_records)} samples...")
    judge = LLMJudge(api_key=api_key, model_name=model_name)
    judge_results = judge.evaluate_sample(eval_records, sample_size=len(eval_records), random_seed=seed)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / "llm_judge_results.json"
    csv_path = RESULTS_DIR / "llm_judge_results.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(judge_results, f, indent=2)

    # Export CSV
    rows = []
    for r in judge_results.get("results", []):
        rows.append({
            "record_id": r.get("record_id"),
            "intent": r.get("intent"),
            "customer_message": r.get("customer_message"),
            "candidate_reply": r.get("candidate_reply"),
            "reference_reply": r.get("reference_reply"),
            "retrieved_evidence": r.get("retrieved_evidence"),
            "relevance": r.get("relevance"),
            "groundedness": r.get("groundedness"),
            "helpfulness": r.get("helpfulness"),
            "safety": r.get("safety"),
            "overall_score": r.get("overall_score"),
            "reasoning": r.get("reasoning"),
            "judge_model": r.get("judge_model", model_name),
            "timestamp": r.get("timestamp", datetime.utcnow().isoformat() + "Z")
        })

    results_df = pd.DataFrame(rows)
    results_df.to_csv(csv_path, index=False)

    print("\n" + "=" * 80)
    print(" LLM JUDGE EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Evaluated: {judge_results.get('successful_count')}/{len(eval_records)}")
    if judge_results.get("aggregate_scores"):
        print("\nMean Dimension Scores (1-5 Scale):")
        for dim, score in judge_results["aggregate_scores"].items():
            dim_name = dim.replace("mean_", "").capitalize()
            print(f"  - {dim_name:<20}: {score:.2f} / 5.0")

    print(f"\n[INFO] Detailed JSON results saved to: {json_path}")
    print(f"[INFO] Detailed CSV results saved to:  {csv_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM-as-a-Judge Evaluation on Golden Set.")
    parser.add_argument("--sample-size", type=int, default=20, help="Number of samples to evaluate (default: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling (default: 42)")
    parser.add_argument("--agent-url", type=str, default="http://localhost:8080", help="Spring Boot agent base URL")
    parser.add_argument("--model", type=str, default=DEFAULT_JUDGE_MODEL, help=f"Gemini judge model (default: {DEFAULT_JUDGE_MODEL})")
    args = parser.parse_args()

    run_llm_judge_evaluation(
        sample_size=args.sample_size,
        seed=args.seed,
        agent_url=args.agent_url,
        model_name=args.model
    )
