# Hiver AI Customer Support Agent

An enterprise-grade, RAG-powered AI Customer Support Agent built with **Java 17 LTS**, **Spring Boot 3.4**, **PostgreSQL 16**, **pgvector**, and **Google Gemini**, accompanied by a reproducible Python 3.11 evaluation framework.

Developed for the **Hiver SDE Intern Take-Home Assignment**.

---

## 1. Problem Statement & Architecture

Customer support operations handle immense volumes of inquiries requiring high-speed classification, grounded troubleshooting advice, and conservative escalation safeguards.

This system provides:
1. **Hybrid Intent Classification**: Classifies customer inquiries into an empirical 10-intent taxonomy discovered from 106K historical `@AppleSupport` conversations in the TWCS dataset.
2. **Grounded RAG Retrieval**: Uses `pgvector` HNSW cosine similarity search over 768-dimensional normalized dense embeddings of past resolutions.
3. **Multi-Tier Escalation Safeguards**: Hard deterministic guardrails for legal threats, account security lockouts, physical damage, and unauthorized billing.
4. **Structured API Responses**: Returns validated replies, confidence scores, escalation reasons, and retrieved historical context without leaking secrets or prompt templates.
5. **Leakage-Isolated Evaluation**: 200-sample stratified golden evaluation set (`data/golden/golden_set.csv`, Seed: 42) with strict tweet ID exclusion guaranteeing 0% data leakage.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SPRING BOOT REST CONTROLLER                     │
│                   POST /api/v1/support · GET /health                  │
├────────────────────────────────────────────────────────────────────────┤
│                          SUPPORT ORCHESTRATOR                          │
│                                                                        │
│  [1. Input Validation & PII Scrubbing]                                 │
│       └─ Strips @mentions, emails, phone numbers, payment cards        │
│                                                                        │
│  [2. pgvector Semantic Vector Retrieval]                              │
│       ├─ Google Gemini gemini-embedding-001 (768-dim dense semantic)   │
│       ├─ HNSW Cosine Similarity Index (<=> vector_cosine_ops)          │
│       ├─ Configurable Similarity Threshold Guardrail (0.35 - 0.65)     │
│       └─ Deterministic Offline Fallback Provider (dim=768)             │
│                                                                        │
│  [3. Hybrid Intent Classification]                                     │
│       └─ Spring AI / Gemini LLM + High-Speed Deterministic Fallback    │
│                                                                        │
│  [4. Grounded Reply Synthesis]                                         │
│       └─ RAG Context Grounding + Character Limit Guardrails            │
│                                                                        │
│  [5. Multi-Tier Escalation Engine]                                     │
│       ├─ Tier 1: Deterministic High-Risk Keyword Guardrails            │
│       ├─ Tier 2: Low-Confidence Threshold Guardrail (< 0.60)           │
│       ├─ Tier 3: High-Risk Intent Policies (Hardware/Security/Billing) │
│       └─ Tier 4: LLM Contextual Triage Fallback                        │
│                                                                        │
│  [6. Response Validation & Safety Guardrails]                          │
│       └─ Prompt leak sanitizer, financial promise blocker              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Quick Start (< 15 Minutes Reproducible Setup)

### Prerequisites
- **Docker & Docker Compose** (for PostgreSQL 16 + pgvector)
- **Java 17 LTS** (Temurin / OpenJDK)
- **Maven 3.9+**
- **Python 3.11+**
- **Google Gemini API Key** (optional for offline testing; required for live semantic embeddings & LLM judge)

---

### Step 1: Start PostgreSQL + pgvector
```bash
docker compose up -d
```
*PostgreSQL is exposed on port `5433` (mapped from container `5432`) to avoid collisions with local Windows postgres instances.*

---

### Step 2: Set Up Python Environment & Seed Retrieval Database

```bash
# Install Python evaluation dependencies
python -m pip install -r evaluation/requirements.txt
```

#### Optional Gemini API Key Configuration
The system works out-of-the-box with deterministic offline fallbacks. To enable live neural embeddings (`gemini-embedding-001`) and live LLM judging:
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"
```
```bash
# Linux / macOS
export GEMINI_API_KEY="your_api_key_here"
```
> [!IMPORTANT]
> The Gemini API key must **never** be hard-coded or committed to git. It is read strictly from the `GEMINI_API_KEY` environment variable.

#### Seed Vector Database
```bash
# Ingests non-golden AppleSupport conversation pairs with 768-dim embeddings into pgvector
python scripts/seed_db.py --sample-size 50 --recreate
```
> [!NOTE]
> **Subsampling Note**: The retrieval database uses a 50-conversation subsample of historical `@AppleSupport` resolutions to remain safely within the Gemini free-tier rate limits (100 RPM / 1,000 RPD) while providing fast (< 1 min) deterministic setup. All 200 golden evaluation records are strictly excluded from ingestion.

---

### Step 3: Run Java Tests & Launch Spring Boot Backend

```bash
cd support-agent
mvn test
mvn spring-boot:run
```
*The Spring Boot REST API starts on `http://localhost:8080`.*

---

### Step 4: Run Complete Evaluation Harness

In a separate terminal:
```bash
python evaluation/run_eval.py
```
This single command executes:
1. Majority Class Trivial Baseline
2. TF-IDF + Logistic Regression ML Baseline
3. Live Spring Boot REST API Evaluation against all 200 golden test cases
4. ROUGE-1 / ROUGE-2 / ROUGE-L reply quality metrics
5. LLM-as-a-Judge evaluation (if `GEMINI_API_KEY` is set)
6. Top 5 Empirical Failure Mode Analysis

---

## 3. REST API Documentation

### Endpoint: `POST /api/v1/support`

- **URL**: `http://localhost:8080/api/v1/support`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`

#### Example Request:
```bash
curl -X POST http://localhost:8080/api/v1/support \
  -H "Content-Type: application/json" \
  -d '{"message": "My iPhone battery is draining very quickly. What can I do?"}'
```

#### Example Response (200 OK):
```json
{
  "intent": "BATTERY_PERFORMANCE",
  "confidence": 0.90,
  "reply": "Battery life is essential; we'll do all we can to help. To start, DM us to let us know the exact iOS version installed: https://t.co/GDrqU22YpT",
  "escalation": {
    "decision": "AUTO_HANDLE",
    "reason": "Standard automated support inquiry resolvable via troubleshooting documentation."
  },
  "similarConversations": [
    {
      "customerText": "Also, since I updated to the new iOS my battery life has been so incredibly bad, wtf @AppleSupport 🙄",
      "agentReply": "Battery life is essential; we'll do all we can to help. To start, DM us to let us know the exact iOS 11 version installed: https://t.co/GDrqU22YpT",
      "intent": "BATTERY_PERFORMANCE",
      "similarityScore": 0.6679
    }
  ]
}
```

### Health Check Endpoint: `GET /api/v1/support/health`
- **Response**: `"AI Support Agent is running"`

---

## 4. Intent Taxonomy (10 Empirically Derived Classes)

Discovered from 106,648 `@AppleSupport` conversation pairs in the TWCS dataset:

1. `SOFTWARE_UPDATE_OS`: iOS/macOS update installations, verification loops, boot issues.
2. `BATTERY_PERFORMANCE`: Rapid drain, charging issues, battery health degradation.
3. `HARDWARE_PHYSICAL_DAMAGE`: Screen cracks, liquid spills, hardware repairs (*Default: ESCALATE*).
4. `ACCOUNT_ACCESS_SECURITY`: Apple ID password resets, 2FA lockouts, stolen devices (*Default: ESCALATE*).
5. `APP_CRASH_PERFORMANCE`: App freezing, unresponsiveness, lag.
6. `NETWORK_CONNECTIVITY`: Wi-Fi disconnects, Bluetooth pairing, cellular signal loss.
7. `BILLING_SUBSCRIPTIONS`: Unauthorized charges, Apple Music billing, refund requests (*Default: ESCALATE*).
8. `AUDIO_SOUND_ISSUES`: Speaker distortion, muffled microphone, earpiece audio.
9. `ICLOUD_STORAGE_SYNC`: iCloud storage full warnings, photo syncing, backups.
10. `GENERAL_PRODUCT_INQUIRY`: Compatibility questions, warranty status, feature inquiries.

---

## 5. Measured Comparative Evaluation Benchmarks

Evaluated against the **200-sample Stratified Golden Evaluation Set** (Seed: 42) with strict 0% data leakage:

| Model / System | Intent Accuracy | Intent Macro F1 | Intent Weighted F1 | Escalation Accuracy | Escalation Macro F1 | ROUGE-1 F1 | ROUGE-L F1 |
|---|---|---|---|---|---|---|---|
| **Majority Baseline** | 0.1050 (10.5%) | 0.0190 | 0.0200 | 0.7000 (70.0%) | 0.4118 | 0.2823 | 0.2282 |
| **ML Baseline (TF-IDF + LogReg)** | 0.4900 (49.0%) | 0.5088 | 0.5128 | 0.7050 (70.5%) | 0.6789 | 0.2905 | 0.2338 |
| **Spring Boot AI Support Agent** | **0.8450 (84.5%)** | **0.8374** | **0.8314** | **0.9350 (93.5%)** | **0.9268** | **0.2745** | **0.2208** |

### Headline Metric: **Intent Macro F1 = 0.8374** & **Escalation Macro F1 = 0.9268**

---

## 6. What is Misleading About My Headline Number?

While the 84.5% intent accuracy and 0.8374 Macro F1 represent strong benchmark performance, several critical nuances must be highlighted:

1. **Stratified Test Set vs Production Class Distribution**:
   The 200-item golden test set was balanced across 10 classes (~14–24 examples per intent). In real-world `@AppleSupport` production traffic, `SOFTWARE_UPDATE_OS` and `BATTERY_PERFORMANCE` account for >60% of volume, while `ICLOUD_STORAGE_SYNC` represents <2%. Macro F1 weights all classes equally, which may obscure real-world high-volume traffic performance.
2. **Small Evaluation Set Size**:
   The 84.5% accuracy is measured on a 200-example manually reviewed golden set. It does not establish proven generalization to long-tail, out-of-distribution queries in high-volume enterprise production.
3. **Retrieval Corpus Size**:
   Semantic retrieval currently operates over a 50-conversation Gemini-embedded subsample due to API quota constraints. While sufficient for demonstration and baseline comparison, it is not the complete 106K historical corpus.
4. **Lexical ROUGE vs Real Support Helpfulness**:
   The ML baseline achieved a slightly higher ROUGE-L (0.2338) than the production agent (0.2208). This occurs because the ML baseline simply copies historical Twitter deflection phrases (*"Please DM us with your model"*), which match historical text lexically but provide poor customer value compared to direct diagnostic instructions.
5. **LLM Judge is a Secondary Diagnostic, Not Ground Truth**:
   The human-vs-LLM agreement analysis revealed weak statistical correlation (see Section 7), demonstrating that LLM judge scores cannot be treated as definitive or validated ground truth.
6. **Escalation Cost Asymmetry**:
   An escalation accuracy of 93.5% does not capture the asymmetry of failure risk: a False Positive (escalating an auto-resolvable battery tip) merely costs a few minutes of human labor, whereas a False Negative (auto-handling billing fraud or swelling battery hardware) can cause severe legal, safety, or financial liability.

---

## 7. LLM-as-a-Judge & Human Agreement Framework

### 4-Dimension Rubric (1–5 Integer Scale)
1. **Relevance (1–5)**: Does the reply directly address the customer's stated issue?
2. **Groundedness (1–5)**: Is the reply supported by retrieved historical evidence and standard Apple guidance without hallucination?
3. **Helpfulness (1–5)**: Does it provide clear, actionable diagnostic steps or legitimate settings paths?
4. **Safety / Escalation (1–5)**: Does it avoid unauthorized financial promises and appropriately escalate sensitive cases?

### LLM Judge Evaluation Results (19/20 Evaluated, 1 Excluded Due to API Rate Limiting)
- **Relevance Mean**: 2.68 / 5.0
- **Groundedness Mean**: 4.16 / 5.0
- **Helpfulness Mean**: 2.26 / 5.0
- **Safety Mean**: 4.32 / 5.0
- **Overall Mean**: 3.35 / 5.0

### Human vs LLM Statistical Agreement ($N=19$ Valid Pairs, 1 Excluded)

```bash
# Calculate statistical agreement
python evaluation/calculate_judge_agreement.py
```

| Dimension | Valid N | Missing | Exact % | Within-1 % | MAD | Pearson $r$ | Spearman $\rho$ | Quadratic Weighted $\kappa$ | Pass/Fail ($\ge 4.0$) $\kappa$ |
|---|---|---|---|---|---|---|---|---|---|
| **Relevance** | 19 | 1 | 10.5% | 42.1% | 2.26 | -0.226 | -0.195 | -0.055 | -0.108 |
| **Groundedness** | 19 | 1 | 63.2% | 79.0% | 0.84 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Helpfulness** | 19 | 1 | 31.6% | 52.6% | 1.37 | -0.227 | -0.188 | -0.111 | 0.038 |
| **Safety** | 19 | 1 | 52.6% | 84.2% | 0.68 | 0.000 | 0.000 | 0.000 | 0.000 |
| **Overall Score** | 19 | 1 | 36.8% | 52.6% | 1.29 | -0.234 | -0.203 | -0.004 | -0.105 |

> [!WARNING]
> **Interpretation & Scientific Integrity**: Human-LLM agreement on this 19-sample validation set is **weak** ($\kappa \le 0.000$, negative correlation). The LLM judge frequently penalizes replies that invite users to DM or ask for iOS versions, whereas human raters recognize this as standard Twitter support procedure. **The LLM judge is therefore presented strictly as an experimental secondary diagnostic, not as a validated ground truth.**

---

## 8. Top 5 Empirical Failure Modes & Diagnoses

Based on empirical error analysis from the 200 golden set predictions:

### 1. Multi-Intent & Compound Queries
- **Real Example (ID 1455307)**: *"IOS 11 is the worst update to date. My phone is useless without WiFi and battery dies in 2 hours."*
- **Observed Behavior**: Classified as `SOFTWARE_UPDATE_OS` (Expected: `SOFTWARE_UPDATE_OS / BATTERY_PERFORMANCE`).
- **Why It Fails**: The single-label classification model is forced to truncate secondary intents.
- **Plausible Hypothesis**: Surface keywords for OS updates dominate attention over downstream battery symptoms.
- **One-Week Improvement**: Implement multi-label intent classification with compound routing and composite troubleshooting guidance.

### 2. Context-Free Follow-up & Attachment Ambiguity
- **Real Example (ID 1516175)**: *"#iOS11 #update #iphoneissueswithIOS11 https://t.co/YhBerEXfFU"*
- **Observed Behavior**: Classified as `GENERAL_PRODUCT_INQUIRY` (Expected: `SOFTWARE_UPDATE_OS`).
- **Why It Fails**: Text contains only hashtags and an image attachment link (`https://t.co`) without clarifying textual context.
- **Plausible Hypothesis**: Missing multimodal analysis and thread context makes image-only tweets ambiguous.
- **One-Week Improvement**: Ingest parent tweet thread context and integrate a vision LLM for screenshot OCR and diagnostics.

### 3. Colloquial Slang, Typos & Non-Standard Lexicon
- **Real Example (ID 582732)**: *"What an utter piece of shit is @AppleSupport latest High Sierra update. My computer never felt so slow before"*
- **Observed Behavior**: Classified as `APP_CRASH_PERFORMANCE` (Expected: `SOFTWARE_UPDATE_OS`).
- **Why It Fails**: Profanity and emotional language alter token embeddings away from standard technical terminology.
- **Plausible Hypothesis**: Emotion-heavy slang dilutes domain n-grams.
- **One-Week Improvement**: Fine-tune dense semantic embeddings and add sentiment-aware prompt grounding.

### 4. Subtle Financial / Security Escalation Boundaries
- **Real Example (ID 2291591)**: *"wanna explain why I just got the 8 plus but I don't have the new emojis and I can't update to get them?"*
- **Observed Behavior**: Classified as `SOFTWARE_UPDATE_OS` instead of `GENERAL_PRODUCT_INQUIRY`.
- **Why It Fails**: Semantic overlap between OS update features and product inquiries creates boundary ambiguity.
- **Plausible Hypothesis**: Feature-level queries lack explicit keyword triggers.
- **One-Week Improvement**: Introduce hierarchical classification (Category $\rightarrow$ Subcategory $\rightarrow$ Escalation policy).

### 5. Generic Historical Boilerplate Retrieval
- **Real Example (ID 1455307)**: Retrieved reply: *"We'd love to help. To start, please send us a DM with more details..."*
- **Observed Behavior**: Agent retrieves generic Twitter DM deflections rather than actionable settings links.
- **Why It Fails**: Historical Twitter dataset contains character-constrained deflection tweets.
- **Plausible Hypothesis**: Retrieval ranks raw tweet frequency over technical specificity.
- **One-Week Improvement**: Ingest and prioritize verified Apple Support Knowledge Base articles over raw tweets in pgvector.

---

## 9. One-More-Week Engineering Plan

If given one additional week, the prioritized roadmap is:

1. **Expand Retrieval Corpus (P1)**: Scale pgvector ingestion from 50 to 2,500+ conversations using rate-budgeted batching.
2. **Knowledge Base Ingestion & Reranking (P1)**: Synthesize structured RAG knowledge chunks from official `support.apple.com` documentation rather than raw tweets, adding reciprocal rank fusion (RRF) reranking.
3. **Multi-Label & Compound Intent Support (P2)**: Implement multi-label classification to support compound customer issues (e.g. OS Update + Battery Drain).
4. **Conversation Thread & Vision Multimodal Ingestion (P2)**: Ingest full parent tweet conversation history and add Gemini Vision screenshot OCR for image attachment URLs (`https://t.co`).
5. **Escalation Guardrail Refinement (P3)**: Add fine-grained financial/security boundary classifiers to eliminate edge-case false negatives.
6. **Scaled Double-Annotated Golden Set (P3)**: Expand the evaluation dataset to 500+ samples with independent dual-annotator inter-rater reliability.
7. **Re-run LLM Judge Validation with Independent Human Raters (P3)**: Collect multi-annotator human ratings across 100+ samples to establish statistically robust human-judge calibration.

---

## 10. Submission Verification Summary

- **Java Suite**: 29/29 JUnit 5 & Mockito test suite passing cleanly (`cd support-agent && mvn test`).
- **Python Suite**: 18/18 unit tests passing cleanly (`python -m unittest discover -s evaluation/tests -p "test_*.py"`).
- **Security Check**: Verified 0 hard-coded secrets or API keys in repository source code; comprehensive `.gitignore` in place.
- **Reproducibility**: Complete evaluation harness runs in a single command (`python evaluation/run_eval.py`).

---

## 11. Key Project Artifacts

- [DECISION_LOG.md](DECISION_LOG.md) — 13 detailed engineering decisions, alternatives, and trade-offs.
- [report/final_report.md](report/final_report.md) — Comprehensive technical evaluation report with verified numbers.
- [data/golden/labelling_guide.md](data/golden/labelling_guide.md) — Intent taxonomy and annotation protocol.
- [evaluation/results/evaluation_summary.json](evaluation/results/evaluation_summary.json) — Machine-readable evaluation metrics.
- [evaluation/results/judge_agreement_summary.md](evaluation/results/judge_agreement_summary.md) — Statistical human-vs-LLM agreement report.
