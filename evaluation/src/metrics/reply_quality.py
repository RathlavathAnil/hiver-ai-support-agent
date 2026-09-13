"""
Reply Quality Evaluation: Lexical Metrics & Limitations
======================================================
Computes ROUGE-1, ROUGE-2, ROUGE-L, length ratio, and lexical overlap.
Explains why lexical metrics alone do not capture customer support quality.
"""

import numpy as np
from typing import Dict, List, Any
from rouge_score import rouge_scorer


def compute_reply_quality_metrics(
    candidate_replies: List[str],
    reference_replies: List[str]
) -> Dict[str, Any]:
    """Computes ROUGE scores and text statistics across candidate vs reference pairs."""
    if len(candidate_replies) != len(reference_replies):
        raise ValueError("Candidate and reference reply lists must have identical lengths.")

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    r1_p, r1_r, r1_f = [], [], []
    r2_p, r2_r, r2_f = [], [], []
    rL_p, rL_r, rL_f = [], [], []
    cand_lens, ref_lens, length_ratios = [], [], []

    for cand, ref in zip(candidate_replies, reference_replies):
        cand_clean = cand.strip() if cand else ""
        ref_clean = ref.strip() if ref else ""

        scores = scorer.score(ref_clean, cand_clean)

        r1_p.append(scores["rouge1"].precision)
        r1_r.append(scores["rouge1"].recall)
        r1_f.append(scores["rouge1"].fmeasure)

        r2_p.append(scores["rouge2"].precision)
        r2_r.append(scores["rouge2"].recall)
        r2_f.append(scores["rouge2"].fmeasure)

        rL_p.append(scores["rougeL"].precision)
        rL_r.append(scores["rougeL"].recall)
        rL_f.append(scores["rougeL"].fmeasure)

        c_words = len(cand_clean.split())
        r_words = len(ref_clean.split())
        cand_lens.append(c_words)
        ref_lens.append(r_words)
        length_ratios.append(c_words / max(1, r_words))

    return {
        "rouge1": {
            "precision": float(np.mean(r1_p)),
            "recall": float(np.mean(r1_r)),
            "f1": float(np.mean(r1_f))
        },
        "rouge2": {
            "precision": float(np.mean(r2_p)),
            "recall": float(np.mean(r2_r)),
            "f1": float(np.mean(r2_f))
        },
        "rougeL": {
            "precision": float(np.mean(rL_p)),
            "recall": float(np.mean(rL_r)),
            "f1": float(np.mean(rL_f))
        },
        "avg_candidate_word_count": float(np.mean(cand_lens)),
        "avg_reference_word_count": float(np.mean(ref_lens)),
        "avg_length_ratio": float(np.mean(length_ratios)),
        "lexical_critique": (
            "Lexical overlap metrics (ROUGE/BLEU) penalize semantically valid, helpful support replies "
            "that use alternative phrasing, newer documentation URLs, or more structured diagnostic steps. "
            "High ROUGE may simply reward copying generic boilerplate ('Please DM us'), while failing to evaluate "
            "groundedness, factual accuracy, safety, and problem resolution."
        )
    }
