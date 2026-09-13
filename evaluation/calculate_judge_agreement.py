"""
Calculate Statistical Agreement Between Human Ratings and LLM Judge Ratings
=============================================================================
Calculates:
- Exact Agreement Rate (%)
- Within-1-Point Agreement Rate (%)
- Mean Absolute Difference (MAD / MAE)
- Pearson & Spearman Rank Correlation
- Quadratic Weighted Cohen's Kappa (ordinal 1-5 scale)
- Binary Pass/Fail Cohen's Kappa (Pass = score >= 4.0)

Usage:
    python evaluation/calculate_judge_agreement.py [--human-csv evaluation/data/human_judge_ratings.csv] [--llm-csv evaluation/results/llm_judge_results.csv]
"""

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evaluation.src.agreement import compute_comprehensive_judge_agreement

DEFAULT_HUMAN_PATH = ROOT_DIR / "evaluation" / "data" / "human_judge_ratings.csv"
DEFAULT_LLM_PATH = ROOT_DIR / "evaluation" / "results" / "llm_judge_results.csv"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results"


def run_agreement_analysis(human_path: Path, llm_path: Path):
    print("=" * 80)
    print(" STATISTICAL AGREEMENT: HUMAN RATINGS vs LLM-AS-A-JUDGE")
    print("=" * 80)

    if not human_path.exists():
        print(f"[ERROR] Human ratings file not found at {human_path}")
        print("        Generate template or rate records using: python evaluation/rate_human_judge.py")
        sys.exit(1)

    if not llm_path.exists():
        print(f"[ERROR] LLM judge results file not found at {llm_path}")
        print("        Run LLM judge first: python evaluation/run_llm_judge.py --sample-size 20")
        sys.exit(1)

    human_df = pd.read_csv(human_path)
    llm_df = pd.read_csv(llm_path)

    print(f"[INFO] Loaded {len(human_df)} human ratings from {human_path}")
    print(f"[INFO] Loaded {len(llm_df)} LLM judge ratings from {llm_path}")

    # Verify status
    if "rating_status" in human_df.columns:
        statuses = human_df["rating_status"].value_counts().to_dict()
        print(f"[INFO] Human rating status breakdown: {statuses}")

    human_records = human_df.to_dict(orient="records")
    llm_records = llm_df.to_dict(orient="records")

    report = compute_comprehensive_judge_agreement(human_records, llm_records)

    if report.get("status") != "SUCCESS":
        print(f"[ERROR] Failed to compute agreement: {report.get('message')}")
        sys.exit(1)

    sample_size = report["sample_size"]
    total_matched = report.get("total_matched_records", sample_size)
    dim_agreements = report["dimension_agreements"]

    print("\n" + "=" * 80)
    print(f" AGREEMENT SUMMARY ACROSS 4 RUBRIC DIMENSIONS (Valid N={sample_size}/{total_matched})")
    print("=" * 80)
    print(f"{'Dimension':<18} | {'Valid N':<8} | {'Exact %':<8} | {'Within-1 %':<10} | {'MAD':<6} | {'Pearson r':<10} | {'Spearman':<10} | {'Weighted Kappa':<15}")
    print("-" * 98)

    md_table = "| Dimension | Valid N | Missing | Exact % | Within-1 % | MAD | Pearson r | Spearman rho | Quadratic Kappa | Pass/Fail Kappa |\n"
    md_table += "|---|---|---|---|---|---|---|---|---|---|\n"

    for dim, metrics in dim_agreements.items():
        dim_label = dim.replace("_", " ").title()
        v_n = metrics.get('valid_pairs', sample_size)
        m_n = metrics.get('missing_pairs', 0)
        exact_pct = f"{metrics['exact_agreement_rate']*100:.1f}%"
        w1_pct = f"{metrics['within_1_point_rate']*100:.1f}%"
        mad_val = f"{metrics['mean_absolute_difference']:.2f}"
        pearson_val = f"{metrics['pearson_correlation']:.3f}"
        spearman_val = f"{metrics['spearman_correlation']:.3f}"
        qw_kappa = f"{metrics['quadratic_weighted_kappa']:.3f} ({metrics['interpretation']})"
        bin_k = f"{metrics['binary_pass_fail_kappa']:.3f}"

        print(f"{dim_label:<18} | {v_n:<8} | {exact_pct:<8} | {w1_pct:<10} | {mad_val:<6} | {pearson_val:<10} | {spearman_val:<10} | {qw_kappa:<15}")
        md_table += f"| **{dim_label}** | {v_n} | {m_n} | {exact_pct} | {w1_pct} | {mad_val} | {pearson_val} | {spearman_val} | {metrics['quadratic_weighted_kappa']:.3f} | {bin_k} |\n"

    print("-" * 98)
    print(f"\n[NOTE] {report['sample_size_note']}\n")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_out = RESULTS_DIR / "judge_agreement_report.json"
    md_out = RESULTS_DIR / "judge_agreement_summary.md"

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(md_out, "w", encoding="utf-8") as f:
        f.write(f"""# Human vs LLM Judge Statistical Agreement Report

*Evaluated on N={sample_size} valid paired records (out of {total_matched} matched samples; Seed: 42).*
*Note: {report['sample_size_note']}*

## Rubric Agreement Matrix

{md_table}

## Metric Definitions
1. **Exact %**: Proportion of examples where Human and LLM assigned the exact same integer rating (1-5).
2. **Within-1 %**: Proportion of ratings differing by $\\le 1.0$ point.
3. **MAD (Mean Absolute Difference)**: Average absolute divergence between ratings $\\frac{{1}}{{N}}\\sum |H_i - L_i|$.
4. **Pearson $r$ & Spearman $\\rho$**: Linear and monotonic rank correlation coefficients.
5. **Quadratic Weighted Cohen's Kappa**: Inter-rater reliability metric penalizing large ordinal disagreements.
6. **Binary Pass/Fail Kappa**: Cohen's Kappa on binary quality threshold ($Score \\ge 4.0$).
""")

    print(f"[INFO] Agreement metrics exported to: {json_out}")
    print(f"[INFO] Summary markdown report saved to: {md_out}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute agreement between Human and LLM Judge ratings.")
    parser.add_argument("--human-csv", type=Path, default=DEFAULT_HUMAN_PATH, help="Path to human ratings CSV")
    parser.add_argument("--llm-csv", type=Path, default=DEFAULT_LLM_PATH, help="Path to LLM judge results CSV")
    args = parser.parse_args()

    run_agreement_analysis(args.human_csv, args.llm_csv)
