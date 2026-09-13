# Hiver AI Customer Support Agent — Technical Evaluation Report

**Candidate Take-Home Assignment**: SDE Intern (AI Support Agent)  
**Target Brand**: `@AppleSupport` | **Dataset**: Customer Support on Twitter (TWCS)  
**Production Stack**: Java 17 LTS · Spring Boot 3.4 · PostgreSQL 16 · pgvector · Gemini API  
**Evaluation Framework**: Python 3.11 · scikit-learn · pandas · ROUGE · LLM-as-a-Judge  

---

## 1. Executive Summary & Problem Framing

Customer support operations at scale face two critical challenges:
1. **Deflection Inefficiency**: Repetitive, generic deflection boilerplate (*"Please send us a DM"*) that degrades customer satisfaction.
2. **Asymmetric Risk on Escalations**: Automated false negatives on dangerous issues (account breaches, unauthorized billing, swelling batteries, legal threats) create catastrophic trust and safety liabilities.

This project delivers an end-to-end AI support agent that:
- **Classifies customer intent** across an empirically discovered 10-class taxonomy grounded in 106K `@AppleSupport` conversations.
- **Retrieves relevant past resolutions** via a `pgvector` HNSW cosine similarity search over 768-dimensional normalized dense embeddings.
- **Enforces conservative multi-tier escalation** combining deterministic keyword guardrails, confidence thresholding, and intent safety policies.
- **Is rigorously benchmarked** against a 200-example stratified golden evaluation set with strict 0% data leakage.

---

## 2. Dataset Profiling & Empirical Intent Discovery

Analysis of the 2.81M tweet Customer Support on Twitter (TWCS) dataset identified `@AppleSupport` as the optimal brand for self-contained support automation:
- **106,648 direct customer-brand conversation pairs** across 76,366 unique customers.
- Selected based on conversation volume, direct customer-brand interactions, multi-turn support patterns, and the presence of actionable troubleshooting resolutions.
- **10 Empirically Derived Intents**:
  1. `SOFTWARE_UPDATE_OS`: iOS/macOS update installations, verification loops, post-update glitches.
  2. `BATTERY_PERFORMANCE`: Rapid battery drain, charging issues, battery health degradation.
  3. `HARDWARE_PHYSICAL_DAMAGE`: Screen cracks, liquid damage, Genius Bar repair inquiries (*Default: ESCALATE*).
  4. `ACCOUNT_ACCESS_SECURITY`: Apple ID lockouts, 2FA codes, password resets, stolen devices (*Default: ESCALATE*).
  5. `APP_CRASH_PERFORMANCE`: App freezing, unresponsiveness, camera/app crashes, lag.
  6. `NETWORK_CONNECTIVITY`: Wi-Fi disconnects, Bluetooth pairing, cellular signal loss, AirDrop.
  7. `BILLING_SUBSCRIPTIONS`: Unauthorized charges, Apple Music billing, refund requests (*Default: ESCALATE*).
  8. `AUDIO_SOUND_ISSUES`: Speaker distortion, muffled microphone, earpiece audio, headphone mode.
  9. `ICLOUD_STORAGE_SYNC`: iCloud storage full warnings, photo syncing, backup restoration.
  10. `GENERAL_PRODUCT_INQUIRY`: Compatibility questions, warranty status, feature inquiries.

---

## 3. Measured Comparative Evaluation Benchmark Results

Evaluated against the **200-sample Stratified Golden Evaluation Set** (Seed: 42) with strict 0% data leakage:

| Evaluation Dimension | Majority Baseline | ML Baseline (TF-IDF + LogReg) | Spring Boot AI Support Agent |
|---|---|---|---|
| **Intent Accuracy** | 0.1050 (10.5%) | 0.4900 (49.0%) | **0.8450 (84.5%)** |
| **Intent Macro F1** | 0.0190 | 0.5088 | **0.8374** |
| **Intent Weighted F1** | 0.0200 | 0.5128 | **0.8314** |
| **Escalation Accuracy** | 0.7000 (70.0%) | 0.7050 (70.5%) | **0.9350 (93.5%)** |
| **Escalation Macro F1** | 0.4118 | 0.6789 | **0.9268** |
| **ROUGE-1 F1** | 0.2823 | 0.2905 | **0.2745** |
| **ROUGE-L F1** | 0.2282 | 0.2338 | **0.2208** |

### Benchmark Insights:
1. **Majority Baseline Failure**: Guessing the majority class yields only 10.5% accuracy and 0.0190 Macro F1 on the balanced golden set.
2. **ML Baseline Limits**: TF-IDF + Logistic Regression reaches 49.0% intent accuracy and 0.5088 Macro F1 on this multi-class domain.
3. **AI Support Agent Performance**: The evaluated AI support agent achieves **84.5% Intent Accuracy**, **0.8374 Intent Macro F1**, and **0.9268 Escalation Macro F1**.

---

## 4. What is Misleading About My Headline Number?

1. **Stratified Test Set vs Real-World Class Imbalance**: In real Twitter traffic, `SOFTWARE_UPDATE_OS` and `BATTERY_PERFORMANCE` represent >60% of volume. Macro F1 weights rare classes (`ICLOUD_STORAGE_SYNC` at 2%) equally with dominant classes.
2. **Small Evaluation Sample**: The 84.5% accuracy is measured on a 200-example manually reviewed golden set. It does not establish proven generalization across high-volume enterprise production.
3. **Retrieval Corpus Subsampling**: The retrieval database currently uses a 50-conversation Gemini-embedded subsample due to API rate constraints.
4. **Lexical ROUGE vs Support Quality**: The ML baseline achieved a slightly higher ROUGE-L (0.2338) than the evaluated agent (0.2208) because it copies legacy Twitter boilerplate (*"Please DM us with your model"*), which matches historical tweets lexically but provides inferior customer value compared to direct troubleshooting guidance.
5. **LLM Judge Disagreement**: The human-vs-LLM agreement analysis revealed weak correlation ($\kappa \le 0.000$), demonstrating that LLM judge scores cannot be treated as ground truth.

---

## 5. LLM-as-a-Judge & Human Agreement Analysis

### Rubric & Mean Scores ($N=19$ Evaluated Samples, 1 Excluded Due to API Rate Limiting)
- **Relevance Mean**: 2.68 / 5.0
- **Groundedness Mean**: 4.16 / 5.0
- **Helpfulness Mean**: 2.26 / 5.0
- **Safety Mean**: 4.32 / 5.0
- **Overall Composite Mean**: 3.35 / 5.0

### Human vs LLM Statistical Agreement ($N=19$ Valid Pairs, 1 Excluded)

| Dimension | Valid N | Missing | Exact % | Within-1 % | MAD | Pearson $r$ | Spearman $\rho$ | Quadratic Weighted $\kappa$ | Pass/Fail ($\ge 4.0$) $\kappa$ |
|---|---|---|---|---|---|---|---|---|---|
| **Relevance** | 19 | 1 | 10.5% | 42.1% | 2.26 | -0.226 | -0.195 | -0.055 | -0.108 |
| **Groundedness** | 19 | 1 | 63.2% | 79.0% | 0.84 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Helpfulness** | 19 | 1 | 31.6% | 52.6% | 1.37 | -0.227 | -0.188 | -0.111 | 0.038 |
| **Safety** | 19 | 1 | 52.6% | 84.2% | 0.68 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Overall Score** | 19 | 1 | 36.8% | 52.6% | 1.29 | -0.234 | -0.203 | -0.004 | -0.105 |

The human ratings used in this analysis were author-provided validation ratings rather than independently double-annotated ratings. Therefore, these agreement statistics are exploratory evidence about judge behavior, not a formal independent human-LLM validation study.

> [!NOTE]
> **Scientific Integrity**: Human-LLM agreement on this 19-sample validation set is weak ($\kappa \le 0.000$). The LLM judge frequently penalizes standard Twitter support procedures (e.g. asking for the iOS version in DM). The LLM judge is therefore treated strictly as a secondary diagnostic, not as ground truth.

---

## 6. Top 5 Empirical Failure Modes & Diagnoses

1. **Multi-Intent & Compound Queries** (e.g. *"IOS 11 is the worst update to date. My phone is useless without WiFi and battery dies in 2 hours."*):
   - *Root Cause*: Single-label classification assigns `SOFTWARE_UPDATE_OS`, neglecting secondary symptoms.
   - *Hypothesis*: Surface update keywords dominate classifier attention.
   - *One-Week Improvement*: Implement multi-label intent classification with compound routing and composite troubleshooting guidance.
2. **Context-Free Follow-ups & Image-Only Tweets** (e.g. *"#iOS11 #update #iphoneissueswithIOS11 https://t.co/..."*):
   - *Root Cause*: Lack of visual screenshot OCR and parent thread context.
   - *Hypothesis*: Tweets containing only hashtags and links lack sufficient lexical tokens for text classifiers.
   - *One-Week Improvement*: Ingest parent tweet thread context and integrate vision LLM for screenshot OCR and diagnostics.
3. **Colloquial Slang, Typos & Non-Standard Lexicon** (e.g. *"What an utter piece of shit is @AppleSupport latest High Sierra update. My computer never felt so slow before"*):
   - *Root Cause*: Profanity and emotional language alter token embeddings away from technical terminology.
   - *Hypothesis*: Emotion-heavy slang dilutes domain n-grams.
   - *One-Week Improvement*: Fine-tune dense semantic embeddings and add sentiment-aware prompt grounding.
4. **Subtle Financial / Security Escalation Boundaries** (e.g. *"wanna explain why I just got the 8 plus but I don't have the new emojis and I can't update to get them?"*):
   - *Root Cause*: Ambiguous boundary between general product inquiry and OS update troubleshooting.
   - *Hypothesis*: Feature-level queries lack explicit keyword triggers.
   - *One-Week Improvement*: Introduce hierarchical classification (Category $\rightarrow$ Subcategory $\rightarrow$ Escalation policy).
5. **Generic Historical Boilerplate Retrieval** (e.g. *"We'd love to help. To start, please send us a DM with more details..."*):
   - *Root Cause*: Historical Twitter dataset contains character-constrained deflection tweets.
   - *Hypothesis*: Retrieval ranks raw tweet frequency over technical specificity.
   - *One-Week Improvement*: Ingest and prioritize verified Apple Support Knowledge Base articles over raw tweets in pgvector.

---

## 7. One-More-Week Engineering Improvement Plan

1. **Expand Retrieval Corpus (P1)**: Scale pgvector ingestion to 2,500+ conversations using rate-budgeted batching.
2. **Knowledge Base Ingestion & Reranking (P1)**: Ingest structured RAG knowledge chunks from official Apple Support documentation with reciprocal rank fusion (RRF).
3. **Multi-Label Intent Handling (P2)**: Support composite routing for compound customer queries.
4. **Conversation Thread & Vision OCR (P2)**: Ingest prior conversation turns and implement screenshot OCR for image attachment URLs (`https://t.co`).
5. **Escalation Boundary Hardening (P3)**: Add specialized classifiers for subtle financial and account security edge cases.
6. **Scaled Double-Annotated Evaluation Set (P3)**: Expand the golden evaluation set to 500+ samples with independent dual-annotator verification.
7. **Calibrate LLM Judge with Independent Raters (P3)**: Conduct multi-annotator human reviews across 100+ samples to calibrate judge rubrics.
