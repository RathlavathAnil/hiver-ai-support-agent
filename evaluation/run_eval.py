"""
Comprehensive Evaluation Harness for Hiver AI Customer Support Agent
====================================================================
Single command execution:
    python evaluation/run_eval.py [--agent-url http://localhost:8080] [--max-train 10000]

Evaluates:
1. Baseline 1: Majority-Class Trivial Baseline
2. Baseline 2: TF-IDF + Logistic Regression ML Baseline
3. Production AI Support Agent (via live REST API)
4. Comprehensive Metrics: Accuracy, Macro F1, ROUGE-L, Escalation F1
5. LLM-as-a-Judge Evaluation & Human Agreement
6. Top 5 Empirical Failure Modes
"""

import os
import sys
import json
import time
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.src.baselines.trivial_baseline import TrivialBaseline
from evaluation.src.baselines.ml_baseline import MLBaseline
from evaluation.src.agent_client import AgentClient
from evaluation.src.metrics.intent_metrics import compute_intent_metrics, compute_escalation_metrics
from evaluation.src.metrics.reply_quality import compute_reply_quality_metrics
from evaluation.src.metrics.llm_judge import LLMJudge
from evaluation.src.agreement import compute_agreement
from evaluation.src.failure_analysis import run_failure_analysis

GOLDEN_CSV_PATH = Path(__file__).parent.parent / "data" / "golden" / "golden_set.csv"
RAW_DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "twcs.csv"
GOLDEN_IDS_PATH = Path(__file__).parent.parent / "data" / "golden" / "golden_tweet_ids.txt"
RESULTS_DIR = Path(__file__).parent / "results"


def load_training_data(max_train_samples: int = 10000) -> pd.DataFrame:
    """Loads non-golden AppleSupport conversation pairs for baseline training."""
    print(f"[INFO] Loading non-golden training data from {RAW_DATA_PATH}...")
    
    # Load golden tweet IDs to prevent data leakage
    excluded_ids = set()
    if GOLDEN_IDS_PATH.exists():
        with open(GOLDEN_IDS_PATH, "r", encoding="utf-8") as f:
            excluded_ids = {line.strip() for line in f if line.strip()}

    df = pd.read_csv(RAW_DATA_PATH)
    apple_out = df[(df["inbound"] == False) & (df["author_id"] == "AppleSupport")]
    pairs = apple_out.merge(
        df[["tweet_id", "author_id", "text", "in_response_to_tweet_id"]],
        left_on="in_response_to_tweet_id",
        right_on="tweet_id",
        suffixes=("_apple", "_customer")
    )

    # Filter out golden tweet IDs (0% leakage)
    pairs["tweet_id_cust_str"] = pairs["tweet_id_customer"].astype(str)
    pairs = pairs[~pairs["tweet_id_cust_str"].isin(excluded_ids)].copy()

    # Preprocess text
    pairs["customer_text"] = pairs["text_customer"].fillna("").astype(str)
    pairs["agent_reply"] = pairs["text_apple"].fillna("").astype(str)

    # Heuristic intent labeling for ML baseline training corpus
    from scripts.seed_db import classify_intent_heuristic
    pairs["intent"] = pairs["customer_text"].apply(classify_intent_heuristic)

    if max_train_samples and max_train_samples < len(pairs):
        pairs = pairs.sample(n=max_train_samples, random_state=42)

    print(f"[INFO] Prepared {len(pairs):,} non-golden training pairs for ML baseline.")
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Run complete evaluation suite against Golden Set.")
    parser.add_argument("--agent-url", type=str, default="http://localhost:8080", help="Spring Boot agent base URL")
    parser.add_argument("--max-train", type=int, default=10000, help="Max training samples for ML baseline")
    parser.add_argument("--skip-agent", action="store_true", help="Skip Spring Boot agent evaluation")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(" HIVER AI CUSTOMER SUPPORT AGENT — COMPREHENSIVE EVALUATION HARNESS")
    print("=" * 80)

    # 1. Load Golden Test Set
    if not GOLDEN_CSV_PATH.exists():
        print(f"[ERROR] Golden evaluation set not found at {GOLDEN_CSV_PATH}")
        sys.exit(1)

    golden_df = pd.read_csv(GOLDEN_CSV_PATH)
    print(f"[INFO] Loaded {len(golden_df)} golden evaluation records from {GOLDEN_CSV_PATH}")

    # Check Human Verification Count
    verified_count = (golden_df.get("label_status", pd.Series()) == "HUMAN_VERIFIED").sum()
    draft_count = len(golden_df) - verified_count
    print(f"[AUDIT] Golden Set Label Status: {verified_count} HUMAN_VERIFIED / {draft_count} DRAFT")

    # 2. Load Training Data for Baselines
    train_df = load_training_data(max_train_samples=args.max_train)

    summary_records = {}

    # =========================================================================
    # 3. BASELINE 1: Trivial Majority-Class Baseline
    # =========================================================================
    print("\n" + "-" * 80)
    print(">>> RUNNING BASELINE 1: TRIVIAL (MAJORITY CLASS)")
    print("-" * 80)
    trivial = TrivialBaseline().fit(train_df)
    trivial_preds = trivial.evaluate_dataset(golden_df)

    y_true_intent = [r["true_intent"] for r in trivial_preds]
    y_pred_intent_triv = [r["predicted_intent"] for r in trivial_preds]
    y_true_dec = [r["true_decision"] for r in trivial_preds]
    y_pred_dec_triv = [r["predicted_decision"] for r in trivial_preds]

    trivial_intent_metrics = compute_intent_metrics(y_true_intent, y_pred_intent_triv)
    trivial_esc_metrics = compute_escalation_metrics(y_true_dec, y_pred_dec_triv)
    trivial_reply_metrics = compute_reply_quality_metrics(
        [r["predicted_reply"] for r in trivial_preds],
        [r["reference_reply"] for r in trivial_preds]
    )

    summary_records["Trivial Baseline (Majority)"] = {
        "intent_accuracy": trivial_intent_metrics["accuracy"],
        "intent_macro_f1": trivial_intent_metrics["macro_f1"],
        "intent_weighted_f1": trivial_intent_metrics["weighted_f1"],
        "escalation_accuracy": trivial_esc_metrics["accuracy"],
        "escalation_macro_f1": trivial_esc_metrics["macro_f1"],
        "rouge1_f1": trivial_reply_metrics["rouge1"]["f1"],
        "rouge2_f1": trivial_reply_metrics["rouge2"]["f1"],
        "rougeL_f1": trivial_reply_metrics["rougeL"]["f1"]
    }

    print(f"  Accuracy:         {trivial_intent_metrics['accuracy']:.4f}")
    print(f"  Macro F1:         {trivial_intent_metrics['macro_f1']:.4f}")
    print(f"  Escalation F1:    {trivial_esc_metrics['macro_f1']:.4f}")
    print(f"  ROUGE-L F1:       {trivial_reply_metrics['rougeL']['f1']:.4f}")

    with open(RESULTS_DIR / "trivial_baseline_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "intent_metrics": trivial_intent_metrics,
            "escalation_metrics": trivial_esc_metrics,
            "reply_quality": trivial_reply_metrics,
            "predictions": trivial_preds
        }, f, indent=2)

    # =========================================================================
    # 4. BASELINE 2: ML Baseline (TF-IDF + Logistic Regression)
    # =========================================================================
    print("\n" + "-" * 80)
    print(">>> RUNNING BASELINE 2: ML (TF-IDF + LOGISTIC REGRESSION)")
    print("-" * 80)
    ml_baseline = MLBaseline(random_state=42).fit(train_df)
    ml_preds = ml_baseline.evaluate_dataset(golden_df)

    y_pred_intent_ml = [r["predicted_intent"] for r in ml_preds]
    y_pred_dec_ml = [r["predicted_decision"] for r in ml_preds]

    ml_intent_metrics = compute_intent_metrics(y_true_intent, y_pred_intent_ml)
    ml_esc_metrics = compute_escalation_metrics(y_true_dec, y_pred_dec_ml)
    ml_reply_metrics = compute_reply_quality_metrics(
        [r["predicted_reply"] for r in ml_preds],
        [r["reference_reply"] for r in ml_preds]
    )

    summary_records["ML Baseline (TF-IDF + LogReg)"] = {
        "intent_accuracy": ml_intent_metrics["accuracy"],
        "intent_macro_f1": ml_intent_metrics["macro_f1"],
        "intent_weighted_f1": ml_intent_metrics["weighted_f1"],
        "escalation_accuracy": ml_esc_metrics["accuracy"],
        "escalation_macro_f1": ml_esc_metrics["macro_f1"],
        "rouge1_f1": ml_reply_metrics["rouge1"]["f1"],
        "rouge2_f1": ml_reply_metrics["rouge2"]["f1"],
        "rougeL_f1": ml_reply_metrics["rougeL"]["f1"]
    }

    print(f"  Accuracy:         {ml_intent_metrics['accuracy']:.4f}")
    print(f"  Macro F1:         {ml_intent_metrics['macro_f1']:.4f}")
    print(f"  Escalation F1:    {ml_esc_metrics['macro_f1']:.4f}")
    print(f"  ROUGE-L F1:       {ml_reply_metrics['rougeL']['f1']:.4f}")

    with open(RESULTS_DIR / "ml_baseline_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "intent_metrics": ml_intent_metrics,
            "escalation_metrics": ml_esc_metrics,
            "reply_quality": ml_reply_metrics,
            "predictions": ml_preds
        }, f, indent=2)

    # =========================================================================
    # 5. PRODUCTION AI SUPPORT AGENT (Spring Boot REST API)
    # =========================================================================
    agent_client = AgentClient(base_url=args.agent_url)
    agent_available = False
    agent_preds = None

    if not args.skip_agent:
        print("\n" + "-" * 80)
        print(f">>> CHECKING SPRING BOOT AGENT API AT {args.agent_url}...")
        print("-" * 80)
        agent_available = agent_client.check_health()

        if agent_available:
            print("[INFO] Spring Boot AI Support Agent is HEALTHY & LIVE! Running evaluation...")
            agent_preds = agent_client.evaluate_dataset(golden_df)
            y_pred_intent_agent = [r["predicted_intent"] for r in agent_preds]
            y_pred_dec_agent = [r["predicted_decision"] for r in agent_preds]

            agent_intent_metrics = compute_intent_metrics(y_true_intent, y_pred_intent_agent)
            agent_esc_metrics = compute_escalation_metrics(y_true_dec, y_pred_dec_agent)
            agent_reply_metrics = compute_reply_quality_metrics(
                [r["predicted_reply"] for r in agent_preds],
                [r["reference_reply"] for r in agent_preds]
            )

            summary_records["Spring Boot AI Support Agent"] = {
                "intent_accuracy": agent_intent_metrics["accuracy"],
                "intent_macro_f1": agent_intent_metrics["macro_f1"],
                "intent_weighted_f1": agent_intent_metrics["weighted_f1"],
                "escalation_accuracy": agent_esc_metrics["accuracy"],
                "escalation_macro_f1": agent_esc_metrics["macro_f1"],
                "rouge1_f1": agent_reply_metrics["rouge1"]["f1"],
                "rouge2_f1": agent_reply_metrics["rouge2"]["f1"],
                "rougeL_f1": agent_reply_metrics["rougeL"]["f1"]
            }

            print(f"  Accuracy:         {agent_intent_metrics['accuracy']:.4f}")
            print(f"  Macro F1:         {agent_intent_metrics['macro_f1']:.4f}")
            print(f"  Escalation F1:    {agent_esc_metrics['macro_f1']:.4f}")
            print(f"  ROUGE-L F1:       {agent_reply_metrics['rougeL']['f1']:.4f}")

            with open(RESULTS_DIR / "agent_results.json", "w", encoding="utf-8") as f:
                json.dump({
                    "intent_metrics": agent_intent_metrics,
                    "escalation_metrics": agent_esc_metrics,
                    "reply_quality": agent_reply_metrics,
                    "predictions": agent_preds
                }, f, indent=2)
        else:
            print("[WARN] Spring Boot agent API is not reachable at " + args.agent_url)
            print("[INFO] Run: cd support-agent && mvn spring-boot:run to start live API.")

    # =========================================================================
    # 6. LLM-AS-A-JUDGE EVALUATION
    # =========================================================================
    print("\n" + "-" * 80)
    print(">>> LLM-AS-A-JUDGE EVALUATION")
    print("-" * 80)
    judge = LLMJudge()
    eval_target_preds = agent_preds if agent_preds else ml_preds
    judge_results = judge.evaluate_sample(eval_target_preds, max_samples=30)

    with open(RESULTS_DIR / "llm_judge_results.json", "w", encoding="utf-8") as f:
        json.dump(judge_results, f, indent=2)

    if judge_results.get("is_available"):
        print(f"[INFO] Completed LLM judge evaluation on {judge_results.get('sample_size')} samples.")
        print(json.dumps(judge_results.get("aggregate_scores"), indent=2))
    else:
        print("[INFO] LLM Judge skipped (GEMINI_API_KEY environment variable not set).")
        print("       To run live LLM judge: export GEMINI_API_KEY=your_key")

    # =========================================================================
    # 7. FAILURE ANALYSIS & HEADLINE METRIC
    # =========================================================================
    print("\n" + "-" * 80)
    print(">>> EMPIRICAL FAILURE ANALYSIS (TOP 5 FAILURE MODES)")
    print("-" * 80)
    active_preds = agent_preds if agent_preds else ml_preds
    failure_report = run_failure_analysis(active_preds)

    with open(RESULTS_DIR / "failure_analysis.json", "w", encoding="utf-8") as f:
        json.dump(failure_report, f, indent=2)

    for mode in failure_report["top_5_failure_modes"]:
        print(f"[{mode['id']}] {mode['category']}")
        print(f"    Issue: {mode['description']}")
        print(f"    Fix:   {mode['proposed_fix']}")

    # =========================================================================
    # 8. EXPORT SUMMARY REPORT & COMPARISON TABLE
    # =========================================================================
    summary_df = pd.DataFrame.from_dict(summary_records, orient="index")
    print("\n" + "=" * 80)
    print(" FINAL EVALUATION SUMMARY COMPARISON")
    print("=" * 80)
    print(summary_df.to_string())

    summary_md = f"""# Evaluation Summary Benchmark Report

*Evaluated on 200 Stratified @AppleSupport Golden Set records (Random Seed: 42).*
*Audit Note: Golden labels generated via heuristic stratification; exact Human Verified count: {verified_count}/200.*

## Model Comparison Table

| Model | Intent Accuracy | Intent Macro F1 | Escalation Macro F1 | ROUGE-1 F1 | ROUGE-L F1 |
|---|---|---|---|---|---|
"""
    for model_name, metrics in summary_records.items():
        summary_md += f"| **{model_name}** | {metrics['intent_accuracy']:.4f} | {metrics['intent_macro_f1']:.4f} | {metrics['escalation_macro_f1']:.4f} | {metrics['rouge1_f1']:.4f} | {metrics['rougeL_f1']:.4f} |\n"

    summary_md += f"""
## Headline Metric: Intent Macro F1 ({summary_records.get('Spring Boot AI Support Agent', summary_records.get('ML Baseline (TF-IDF + LogReg)', {})).get('intent_macro_f1', 0.0):.4f})

### What is Misleading About This Headline Number?
1. **Stratified Golden Set vs Real Imbalance**: The 200-sample golden set was sampled across balanced strata (14–24 examples per intent). In production TWCS traffic, `SOFTWARE_UPDATE_OS` and `BATTERY_PERFORMANCE` represent over 60% of real volume. Macro F1 gives equal weight to rare classes (`ICLOUD_STORAGE_SYNC`), potentially exaggerating or masking real-world production performance.
2. **Lexical ROUGE vs Support Quality**: ROUGE scores reward verbatim copying of historical Twitter text (often repetitive 'Please DM us' deflections). A semantically accurate troubleshooting instruction linking to `https://support.apple.com` scores lower on ROUGE than a useless deflection.
3. **Escalation Trade-off (False Positives vs False Negatives)**: High escalation accuracy does not capture the asymmetry of customer risk: auto-handling a cracked screen or billing fraud (False Negative) is catastrophic, whereas escalating an automated query (False Positive) merely costs human labor.
"""

    with open(RESULTS_DIR / "summary_table.md", "w", encoding="utf-8") as f:
        f.write(summary_md)

    with open(RESULTS_DIR / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_records, f, indent=2)

    print(f"\n[INFO] Results successfully saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
