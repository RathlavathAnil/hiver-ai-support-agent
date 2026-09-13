"""
Intent & Escalation Classification Metrics
===========================================
Computes standard classification evaluation metrics:
- Accuracy
- Macro / Weighted Precision, Recall, F1
- Per-class classification report
- Confusion matrix
"""

import numpy as np
from typing import Dict, List, Any
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)


def compute_intent_metrics(y_true: List[str], y_pred: List[str], labels: List[str] = None) -> Dict[str, Any]:
    """Computes comprehensive intent classification metrics."""
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )

    per_class_p, per_class_r, per_class_f1, per_class_supp = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )

    per_intent_breakdown = {}
    for idx, label in enumerate(labels):
        per_intent_breakdown[label] = {
            "precision": float(per_class_p[idx]),
            "recall": float(per_class_r[idx]),
            "f1_score": float(per_class_f1[idx]),
            "support": int(per_class_supp[idx])
        }

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "accuracy": acc,
        "macro_precision": float(p_macro),
        "macro_recall": float(r_macro),
        "macro_f1": float(f1_macro),
        "weighted_precision": float(p_weighted),
        "weighted_recall": float(r_weighted),
        "weighted_f1": float(f1_weighted),
        "per_intent": per_intent_breakdown,
        "labels": labels,
        "confusion_matrix": cm.tolist()
    }


def compute_escalation_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """Computes binary escalation metrics (AUTO_HANDLE vs ESCALATE)."""
    labels = ["AUTO_HANDLE", "ESCALATE"]
    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    p_class, r_class, f1_class, supp_class = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "accuracy": acc,
        "macro_f1": float(f1_macro),
        "per_class": {
            "AUTO_HANDLE": {
                "precision": float(p_class[0]),
                "recall": float(r_class[0]),
                "f1_score": float(f1_class[0]),
                "support": int(supp_class[0])
            },
            "ESCALATE": {
                "precision": float(p_class[1]),
                "recall": float(r_class[1]),
                "f1_score": float(f1_class[1]),
                "support": int(supp_class[1])
            }
        },
        "labels": labels,
        "confusion_matrix": cm.tolist()
    }
