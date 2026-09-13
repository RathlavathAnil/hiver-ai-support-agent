"""
Human vs LLM Agreement Analysis
===============================
Calculates statistical agreement between human annotators and LLM judges across the 4 rubric dimensions:
1. Exact Agreement Rate (% of exact 1-5 score matches)
2. Mean Absolute Difference (MAD / MAE)
3. Pearson & Spearman Rank Correlation
4. Cohen's Kappa (Quadratic weighted for ordinal 1-5 scores & Binary pass/fail for threshold >= 4.0)

Includes clear handling and documentation for small validation sample sizes (e.g. N=20)
and robust exclusion of missing / unrated LLM judge responses without data fabrication.
"""

import warnings
import numpy as np
from typing import Dict, List, Any, Optional, Union
from sklearn.metrics import cohen_kappa_score
from scipy.stats import pearsonr, spearmanr


def is_valid_score(val: Any) -> bool:
    """Checks whether a value is a valid numeric rating (not None, not NaN, not Inf)."""
    if val is None:
        return False
    try:
        f = float(val)
        return not np.isnan(f) and not np.isinf(f)
    except (ValueError, TypeError):
        return False


def get_record_id(record: Dict[str, Any]) -> str:
    """Extracts normalized record ID string from record dictionary."""
    for key in ["record_id", "id", "tweet_id"]:
        if key in record and record[key] is not None:
            val = record[key]
            if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                continue
            s_val = str(val).strip()
            if s_val.endswith(".0") and s_val[:-2].isdigit():
                s_val = s_val[:-2]
            if s_val:
                return s_val
    return ""


def compute_agreement_for_dimension(
    human_scores: List[Any],
    llm_scores: List[Any],
    pass_threshold: float = 4.0
) -> Dict[str, Any]:
    """
    Computes agreement metrics for a single rubric dimension across paired human and LLM ratings.
    Filters out any pairs where either score is missing, NaN, or non-numeric.
    """
    if len(human_scores) != len(llm_scores):
        raise ValueError("Human and LLM score lists must have identical lengths.")

    # Filter only valid numeric pairs
    valid_pairs = [
        (float(h), float(l))
        for h, l in zip(human_scores, llm_scores)
        if is_valid_score(h) and is_valid_score(l)
    ]

    total_submitted = len(human_scores)
    valid_n = len(valid_pairs)
    missing_n = total_submitted - valid_n

    if valid_n == 0:
        return {
            "status": "INSUFFICIENT_DATA",
            "sample_size": 0,
            "valid_pairs": 0,
            "missing_pairs": missing_n,
            "exact_agreement_rate": 0.0,
            "within_1_point_rate": 0.0,
            "mean_absolute_difference": 0.0,
            "pearson_correlation": 0.0,
            "pearson_p_value": 1.0,
            "spearman_correlation": 0.0,
            "spearman_p_value": 1.0,
            "quadratic_weighted_kappa": 0.0,
            "binary_pass_fail_kappa": 0.0,
            "binary_pass_fail_accuracy": 0.0,
            "interpretation": interpret_kappa(0.0)
        }

    h_arr = np.array([p[0] for p in valid_pairs], dtype=float)
    l_arr = np.array([p[1] for p in valid_pairs], dtype=float)

    # 1. Exact Agreement Rate
    exact_matches = int(np.sum(np.round(h_arr) == np.round(l_arr)))
    exact_agreement_rate = round(float(exact_matches / valid_n), 4)

    # 2. Within-1-Point Agreement Rate
    within_1_matches = int(np.sum(np.abs(h_arr - l_arr) <= 1.0))
    within_1_agreement_rate = round(float(within_1_matches / valid_n), 4)

    # 3. Mean Absolute Difference (MAD / MAE)
    mad = round(float(np.mean(np.abs(h_arr - l_arr))), 4)

    # 4. Pearson & Spearman Correlation
    if valid_n > 1 and len(set(h_arr)) > 1 and len(set(l_arr)) > 1:
        try:
            corr_p, p_val_p = pearsonr(h_arr, l_arr)
            corr_s, p_val_s = spearmanr(h_arr, l_arr)
            pearson_corr = round(float(corr_p), 4) if not np.isnan(corr_p) else 0.0
            pearson_p = round(float(p_val_p), 4) if not np.isnan(p_val_p) else 1.0
            spearman_corr = round(float(corr_s), 4) if not np.isnan(corr_s) else 0.0
            spearman_p = round(float(p_val_s), 4) if not np.isnan(p_val_s) else 1.0
        except Exception:
            pearson_corr, pearson_p = 0.0, 1.0
            spearman_corr, spearman_p = 0.0, 1.0
    else:
        pearson_corr, pearson_p = 0.0, 1.0
        spearman_corr, spearman_p = 0.0, 1.0

    # 5. Quadratic Weighted Cohen's Kappa (for ordinal 1-5 scale)
    h_int = [int(round(x)) for x in h_arr]
    l_int = [int(round(x)) for x in l_arr]
    if h_int == l_int:
        qw_kappa = 1.0
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                val = cohen_kappa_score(h_int, l_int, labels=[1, 2, 3, 4, 5], weights="quadratic")
            qw_kappa = round(float(val), 4) if not np.isnan(val) else (1.0 if h_int == l_int else 0.0)
        except Exception:
            qw_kappa = 0.0

    # 6. Binary Pass/Fail Cohen's Kappa (Pass = score >= pass_threshold)
    h_pass = [1 if x >= pass_threshold else 0 for x in h_arr]
    l_pass = [1 if x >= pass_threshold else 0 for x in l_arr]
    bin_accuracy = round(float(sum(1 for h, l in zip(h_pass, l_pass) if h == l) / valid_n), 4)
    if h_pass == l_pass:
        bin_kappa = 1.0
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                val = cohen_kappa_score(h_pass, l_pass, labels=[0, 1])
            bin_kappa = round(float(val), 4) if not np.isnan(val) else (1.0 if h_pass == l_pass else 0.0)
        except Exception:
            bin_kappa = 0.0

    return {
        "status": "SUCCESS",
        "sample_size": valid_n,
        "valid_pairs": valid_n,
        "missing_pairs": missing_n,
        "exact_agreement_rate": exact_agreement_rate,
        "within_1_point_rate": within_1_agreement_rate,
        "mean_absolute_difference": mad,
        "pearson_correlation": pearson_corr,
        "pearson_p_value": pearson_p,
        "spearman_correlation": spearman_corr,
        "spearman_p_value": spearman_p,
        "quadratic_weighted_kappa": qw_kappa,
        "binary_pass_fail_kappa": bin_kappa,
        "binary_pass_fail_accuracy": bin_accuracy,
        "interpretation": interpret_kappa(qw_kappa)
    }


def compute_comprehensive_judge_agreement(
    human_records: List[Dict[str, Any]],
    llm_records: List[Dict[str, Any]],
    dimensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes pairwise agreement across all rubric dimensions and overall composite score.
    Matches records by 'record_id' or 'id'.
    """
    dims = dimensions or ["relevance", "groundedness", "helpfulness", "safety", "overall_score"]
    
    # Index LLM records by record_id
    llm_by_id = {}
    for r in llm_records:
        rid = get_record_id(r)
        if rid:
            llm_by_id[rid] = r

    matched_pairs = []
    for h in human_records:
        rid = get_record_id(h)
        if rid and rid in llm_by_id:
            matched_pairs.append((h, llm_by_id[rid]))

    if not matched_pairs:
        return {
            "status": "NO_MATCHED_PAIRS",
            "message": "No matching record IDs found between human ratings and LLM judge ratings.",
            "total_human_records": len(human_records),
            "total_llm_records": len(llm_records),
            "sample_size": 0,
            "dimension_agreements": {}
        }

    total_matched = len(matched_pairs)
    dim_results = {}
    for dim in dims:
        h_scores = []
        l_scores = []
        for h, l in matched_pairs:
            h_scores.append(h.get(dim))
            l_scores.append(l.get(dim))
        
        dim_results[dim] = compute_agreement_for_dimension(h_scores, l_scores)

    valid_counts = [
        res["valid_pairs"]
        for res in dim_results.values()
        if res.get("status") == "SUCCESS" and res.get("valid_pairs", 0) > 0
    ]
    overall_valid = max(valid_counts) if valid_counts else (
        dim_results.get("overall_score", {}).get("valid_pairs", total_matched if not dims else 0)
    )
    overall_missing = total_matched - overall_valid

    return {
        "status": "SUCCESS",
        "total_human_records": len(human_records),
        "total_llm_records": len(llm_records),
        "total_matched_records": total_matched,
        "sample_size": overall_valid,
        "valid_pairs": overall_valid,
        "missing_pairs": overall_missing,
        "sample_size_note": f"Sample size N={overall_valid} valid pairs ({overall_missing} excluded due to missing LLM ratings) out of {total_matched} matched golden records.",
        "dimension_agreements": dim_results
    }


def compute_agreement(
    human_data: Union[List[float], List[Dict[str, Any]], Any],
    llm_data: Union[List[float], List[Dict[str, Any]], Any],
    pass_threshold: float = 4.0,
    dimensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Unified entry point for computing statistical agreement between human annotators and LLM judges.
    
    Supports:
    - 1D scalar score sequences (computes exact agreement, within-1, MAD, Pearson, Spearman, Kappa)
    - Record lists / datasets with multiple rubric dimensions (relevance, groundedness, helpfulness, safety, overall_score)
    """
    # Handle pandas DataFrame or Series inputs if passed
    if hasattr(human_data, "to_dict") and not hasattr(human_data, "tolist"):
        human_data = human_data.to_dict(orient="records")
    if hasattr(llm_data, "to_dict") and not hasattr(llm_data, "tolist"):
        llm_data = llm_data.to_dict(orient="records")

    # If inputs are lists of dictionaries (or datasets), run comprehensive multi-dimension agreement
    if isinstance(human_data, list) and human_data and isinstance(human_data[0], dict):
        return compute_comprehensive_judge_agreement(
            human_records=human_data,
            llm_records=llm_data,
            dimensions=dimensions
        )

    # Otherwise, treat as 1D score sequences
    h_list = list(human_data) if hasattr(human_data, "__iter__") else [human_data]
    l_list = list(llm_data) if hasattr(llm_data, "__iter__") else [llm_data]
    return compute_agreement_for_dimension(
        human_scores=h_list,
        llm_scores=l_list,
        pass_threshold=pass_threshold
    )


def interpret_kappa(kappa: float) -> str:
    if kappa < 0.0:
        return "Poor agreement (less than chance)"
    elif kappa <= 0.20:
        return "Slight agreement"
    elif kappa <= 0.40:
        return "Fair agreement"
    elif kappa <= 0.60:
        return "Moderate agreement"
    elif kappa <= 0.80:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"


__all__ = [
    "compute_agreement",
    "compute_agreement_for_dimension",
    "compute_comprehensive_judge_agreement",
    "interpret_kappa",
    "is_valid_score",
    "get_record_id"
]

