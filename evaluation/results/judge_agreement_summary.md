# Human vs LLM Judge Statistical Agreement Report

*Evaluated on N=19 valid paired records (out of 20 matched samples; Seed: 42).*
*Note: Sample size N=19 valid pairs (1 excluded due to missing LLM ratings) out of 20 matched golden records.*

## Rubric Agreement Matrix

| Dimension | Valid N | Missing | Exact % | Within-1 % | MAD | Pearson r | Spearman rho | Quadratic Kappa | Pass/Fail Kappa |
|---|---|---|---|---|---|---|---|---|---|
| **Relevance** | 19 | 1 | 10.5% | 42.1% | 2.26 | -0.226 | -0.195 | -0.055 | -0.108 |
| **Groundedness** | 19 | 1 | 63.2% | 79.0% | 0.84 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Helpfulness** | 19 | 1 | 31.6% | 52.6% | 1.37 | -0.227 | -0.188 | -0.111 | 0.038 |
| **Safety** | 19 | 1 | 52.6% | 84.2% | 0.68 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Overall Score** | 19 | 1 | 36.8% | 52.6% | 1.29 | -0.234 | -0.203 | -0.004 | -0.105 |


## Metric Definitions
1. **Exact %**: Proportion of examples where Human and LLM assigned the exact same integer rating (1-5).
2. **Within-1 %**: Proportion of ratings differing by $\le 1.0$ point.
3. **MAD (Mean Absolute Difference)**: Average absolute divergence between ratings $\frac{1}{N}\sum |H_i - L_i|$.
4. **Pearson $r$ & Spearman $\rho$**: Linear and monotonic rank correlation coefficients.
5. **Quadratic Weighted Cohen's Kappa**: Inter-rater reliability metric penalizing large ordinal disagreements.
6. **Binary Pass/Fail Kappa**: Cohen's Kappa on binary quality threshold ($Score \ge 4.0$).
