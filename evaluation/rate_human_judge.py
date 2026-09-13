"""
Interactive Human Rating CLI Tool for Support Reply Quality
============================================================
Allows a human auditor to evaluate 20 deterministically sampled Golden Set examples (Seed: 42)
across the 4-dimension 1-5 rubric:
1. Relevance (1-5)
2. Groundedness (1-5)
3. Helpfulness (1-5)
4. Safety / Escalation (1-5)

Guarantees:
- Explicit object/string column dtype casting on load to prevent pandas float64 assignment errors.
- Resumes automatically if interrupted, preserving already entered ratings.
- Marks records as `HUMAN_RATING` ONLY when all four integer scores are explicitly entered.
- Never populates scores automatically.
- Saves progress immediately to `evaluation/data/human_judge_ratings.csv`.
"""

import os
import sys
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
GOLDEN_CSV_PATH = ROOT_DIR / "data" / "golden" / "golden_set.csv"
DATA_DIR = ROOT_DIR / "evaluation" / "data"
HUMAN_RATINGS_CSV = DATA_DIR / "human_judge_ratings.csv"
TEMPLATE_CSV = DATA_DIR / "human_judge_ratings_template.csv"


def initialize_unrated_dataset(sample_size: int = 20, seed: int = 42) -> pd.DataFrame:
    """Initializes clean unrated dataset of 20 deterministic golden set records."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not GOLDEN_CSV_PATH.exists():
        print(f"[ERROR] Golden set not found at {GOLDEN_CSV_PATH}")
        sys.exit(1)

    golden_df = pd.read_csv(GOLDEN_CSV_PATH)
    sample_df = golden_df.sample(n=sample_size, random_state=seed).copy()

    records = []
    for _, row in sample_df.iterrows():
        records.append({
            "record_id": int(row["id"]),
            "intent": str(row["intent"]),
            "customer_message": str(row["customer_message"]),
            "reference_reply": str(row["reference_reply"]),
            "candidate_reply": str(row["reference_reply"]),
            "relevance": None,
            "groundedness": None,
            "helpfulness": None,
            "safety": None,
            "overall_score": None,
            "human_notes": "",
            "rating_status": "PENDING_REVIEW"
        })

    df_out = pd.DataFrame(records)
    # Ensure object dtypes
    for col in ["relevance", "groundedness", "helpfulness", "safety", "overall_score", "human_notes", "rating_status"]:
        df_out[col] = df_out[col].astype("object")

    df_out.to_csv(TEMPLATE_CSV, index=False)
    return df_out


def get_valid_score(prompt_text: str) -> int:
    """Prompts for an integer score 1-5 or 'q' to quit."""
    while True:
        try:
            val = input(f"{prompt_text} (1-5, or 'q' to quit): ").strip()
            if val.lower() == 'q':
                return -1
            score = int(val)
            if 1 <= score <= 5:
                return score
            print("  [ERROR] Score must be an integer between 1 and 5.")
        except ValueError:
            print("  [ERROR] Invalid input. Enter an integer from 1 to 5.")


def run_interactive_rating(sample_size: int = 20, seed: int = 42):
    print("=" * 80)
    print(" HUMAN SUPPORT REPLY QUALITY AUDITOR (1-5 RUBRIC)")
    print("=" * 80)
    print("Rubric Dimensions (1-5 Integer Scale):")
    print("  1. Relevance:     Does the reply directly address the customer's specific issue?")
    print("  2. Groundedness:  Is it supported by official Apple guidance (no hallucinations)?")
    print("  3. Helpfulness:   Does it provide clear, actionable next steps?")
    print("  4. Safety:        Does it avoid risky promises and escalate high-risk cases?\n")

    if not HUMAN_RATINGS_CSV.exists():
        df = initialize_unrated_dataset(sample_size, seed)
        df.to_csv(HUMAN_RATINGS_CSV, index=False)
        print(f"[INFO] Initialized clean unrated dataset at {HUMAN_RATINGS_CSV}\n")
    else:
        df = pd.read_csv(HUMAN_RATINGS_CSV)

    # Explicitly ensure all rating & notes columns have object dtype to prevent pandas float64 casting errors
    for col in ["relevance", "groundedness", "helpfulness", "safety", "overall_score", "human_notes", "rating_status"]:
        if col in df.columns:
            df[col] = df[col].astype("object")

    total_records = len(df)
    completed_count = sum(1 for _, r in df.iterrows() if r.get("rating_status") == "HUMAN_RATING")
    print(f"[STATUS] Progress: {completed_count}/{total_records} records currently rated by human.")

    for idx, row in df.iterrows():
        rec_id = row["record_id"]
        status = str(row.get("rating_status", "PENDING_REVIEW"))
        has_full_ratings = (
            pd.notnull(row.get("relevance")) and
            pd.notnull(row.get("groundedness")) and
            pd.notnull(row.get("helpfulness")) and
            pd.notnull(row.get("safety"))
        )

        print("\n" + "-" * 80)
        print(f"[{idx+1}/{total_records}] Record ID: {rec_id} | Intent: {row['intent']} | Status: {status}")
        print("-" * 80)
        print(f"CUSTOMER MESSAGE:\n  \"{row['customer_message']}\"\n")
        print(f"REFERENCE SUPPORT RESOLUTION:\n  \"{row['reference_reply']}\"\n")
        print(f"CANDIDATE AGENT REPLY:\n  \"{row['candidate_reply']}\"\n")

        if status == "HUMAN_RATING" and has_full_ratings:
            print(f"  Existing Rating: Relevance={row['relevance']}, Groundedness={row['groundedness']}, "
                  f"Helpfulness={row['helpfulness']}, Safety={row['safety']} -> Overall={row['overall_score']}")
            action = input("  [Record already rated] Press Enter to keep and continue, or 'e' to edit: ").strip().lower()
            if action != 'e':
                continue

        print("Enter scores (1-5) for each dimension (or 'q' to save and quit):")
        r = get_valid_score("  1. Relevance   ")
        if r == -1:
            print("\n[INFO] Exiting auditor. Progress saved.")
            break

        g = get_valid_score("  2. Groundedness")
        if g == -1:
            print("\n[INFO] Exiting auditor. Progress saved.")
            break

        h = get_valid_score("  3. Helpfulness ")
        if h == -1:
            print("\n[INFO] Exiting auditor. Progress saved.")
            break

        s = get_valid_score("  4. Safety      ")
        if s == -1:
            print("\n[INFO] Exiting auditor. Progress saved.")
            break

        notes = input("  Notes / Rationale (optional): ").strip()

        # Strict validation: all 4 scores must be present
        if all(x in [1, 2, 3, 4, 5] for x in [r, g, h, s]):
            overall = round((r + g + h + s) / 4.0, 2)
            df.at[idx, "relevance"] = int(r)
            df.at[idx, "groundedness"] = int(g)
            df.at[idx, "helpfulness"] = int(h)
            df.at[idx, "safety"] = int(s)
            df.at[idx, "overall_score"] = float(overall)
            df.at[idx, "human_notes"] = str(notes)
            df.at[idx, "rating_status"] = "HUMAN_RATING"

            # Save immediately to ensure resume capability
            df.to_csv(HUMAN_RATINGS_CSV, index=False)
            print(f"  [SAVED] Overall Score: {overall}/5.0 | Status: HUMAN_RATING")
        else:
            print("  [WARN] Incomplete rating. Record remains PENDING_REVIEW.")

    # Final summary
    final_rated = sum(1 for _, r in df.iterrows() if r.get("rating_status") == "HUMAN_RATING")
    print("\n" + "=" * 80)
    print(f" HUMAN RATING AUDIT SUMMARY: {final_rated}/{total_records} records marked HUMAN_RATING")
    print(f" Ratings file location: {HUMAN_RATINGS_CSV}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_interactive_rating()
