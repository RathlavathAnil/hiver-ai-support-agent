# Evaluation Summary Benchmark Report

*Evaluated on 200 Stratified @AppleSupport Golden Set records (Random Seed: 42).*
*Audit Note: Golden labels generated via heuristic stratification; exact Human Verified count: 200/200.*

## Model Comparison Table

| Model | Intent Accuracy | Intent Macro F1 | Escalation Macro F1 | ROUGE-1 F1 | ROUGE-L F1 |
|---|---|---|---|---|---|
| **Trivial Baseline (Majority)** | 0.1050 | 0.0190 | 0.4118 | 0.2823 | 0.2282 |
| **ML Baseline (TF-IDF + LogReg)** | 0.4900 | 0.5088 | 0.6789 | 0.2905 | 0.2338 |
| **Spring Boot AI Support Agent** | 0.8450 | 0.8374 | 0.9268 | 0.2745 | 0.2208 |

## Headline Metric: Intent Macro F1 (0.8374)

### What is Misleading About This Headline Number?
1. **Stratified Golden Set vs Real Imbalance**: The 200-sample golden set was sampled across balanced strata (14–24 examples per intent). In production TWCS traffic, `SOFTWARE_UPDATE_OS` and `BATTERY_PERFORMANCE` represent over 60% of real volume. Macro F1 gives equal weight to rare classes (`ICLOUD_STORAGE_SYNC`), potentially exaggerating or masking real-world production performance.
2. **Lexical ROUGE vs Support Quality**: ROUGE scores reward verbatim copying of historical Twitter text (often repetitive 'Please DM us' deflections). A semantically accurate troubleshooting instruction linking to `https://support.apple.com` scores lower on ROUGE than a useless deflection.
3. **Escalation Trade-off (False Positives vs False Negatives)**: High escalation accuracy does not capture the asymmetry of customer risk: auto-handling a cracked screen or billing fraud (False Negative) is catastrophic, whereas escalating an automated query (False Positive) merely costs human labor.
