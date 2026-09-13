# Golden Evaluation Set Specification & Validation Report

**Dataset Version**: `1.0-draft` (Initialized for human verification)  
**File Location**: [`data/golden/golden_set.csv`](../data/golden/golden_set.csv)  
**Total Evaluation Records**: Exactly `200` stratified customer conversations  
**Target Brand**: `@AppleSupport`  
**Random Sampling Seed**: `SEED = 42` (Deterministic and fully reproducible)  
**Annotation Guide**: [`data/golden/labelling_guide.md`](../data/golden/labelling_guide.md)  
**Interactive Labelling Tool**: [`scripts/label_golden_set.py`](../scripts/label_golden_set.py)  

---

## 1. Overview & Evaluation Objective

The Golden Evaluation Set serves as the authoritative, ground truth benchmark for evaluating the Hiver AI Customer Support Agent against two baseline systems:
1. **Trivial Baseline**: Zero-intelligence majority-class predictor.
2. **Traditional ML Baseline**: TF-IDF vectorizer + Logistic Regression / Nearest-Neighbor retriever.
3. **AI Support Agent**: Production Spring Boot 3 + Gemini LLM + pgvector RAG system.

### Principles:
* **True Ground Truth**: Ground truth labels must reflect human judgement rather than synthetic model consensus. Model predictions must **never** serve as gold labels.
* **Controlled Class Balance**: Unlike the raw dataset (where `SOFTWARE_UPDATE_OS` constitutes 27.8% of traffic), the golden set is stratified so that minority and critical safety categories are adequately represented.
* **Strict Evaluation Isolation**: Golden examples must be held out completely to prevent data leakage into vector indices or baseline training sets.

---

## 2. Stratified Sampling Methodology

The 200 records were deterministically sampled from the 106,648 `@AppleSupport` conversation pairs using `SEED=42`.

### Stratification Criteria:
1. **Intent Coverage**: Each of the 10 approved intent categories received between 16 and 24 examples.
2. **Message Length Tiers**:
   - Short messages ($< 70$ characters): ~25% of each stratum.
   - Medium messages (70–140 characters): ~50% of each stratum.
   - Long messages ($> 140$ characters): ~25% of each stratum.
3. **Escalation Coverage**: Intentionally balanced between standard automatable issues (`AUTO_HANDLE`: 70%) and critical human handoffs (`ESCALATE`: 30%).
4. **Linguistic Diversity**: Includes colloquial slang, technical acronyms, spelling errors, punctuation omissions, and multi-turn follow-ups.

---

## 3. Data Leakage Prevention Architecture

To guarantee the validity of downstream benchmark results, the golden evaluation set is strictly isolated:

```
[Raw Customer Support Data: 106,648 pairs]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
[Golden Evaluation Set]    [Development / Indexing Pool]
   (200 Tweet IDs)            (106,448 Tweet IDs)
         │                               │
         ▼                               ▼
  golden_tweet_ids.txt             pgvector HNSW Index
         │                         Baseline Training
         │                         Prompt Few-Shot Examples
         ▼
   STRICT ISOLATION
 (Zero Data Leakage)
```

1. **ID Tracking**: All 200 customer tweet IDs are exported to [`data/golden/golden_tweet_ids.txt`](../data/golden/golden_tweet_ids.txt).
2. **Database Seeding Filter**: The database ingestion script (`scripts/seed_db.py`) explicitly checks this file and skips any tweet whose ID is present.
3. **ML Baseline Exclusion**: The Python evaluation runner (`evaluation/src/baselines/ml_baseline.py`) fits its TF-IDF vectorizer and classifiers strictly on training data that filters out the golden set IDs.

---

## 4. Comprehensive Validation Report

A full validation audit of `data/golden/golden_set.csv` confirms zero missing values, zero duplicates, and balanced distribution across all operational dimensions:

### A. Intent Distribution:

| Intent Identifier | Target Category | Count | Percentage | Default Action |
|---|---|:---:|:---:|:---:|
| `SOFTWARE_UPDATE_OS` | Updates, verification errors & bootloops | 24 | 12.0% | `AUTO_HANDLE` |
| `BATTERY_PERFORMANCE` | Fast drain, charging failures & heat | 22 | 11.0% | `AUTO_HANDLE` |
| `HARDWARE_PHYSICAL_DAMAGE` | Screen cracks, liquid damage & repairs | 20 | 10.0% | `ESCALATE` |
| `ACCOUNT_ACCESS_SECURITY` | Apple ID lock, passcodes & 2FA codes | 20 | 10.0% | `ESCALATE` |
| `APP_CRASH_PERFORMANCE` | App crashing, screen freeze & UI lag | 20 | 10.0% | `AUTO_HANDLE` |
| `NETWORK_CONNECTIVITY` | Wi-Fi disconnect, Bluetooth & cellular | 20 | 10.0% | `AUTO_HANDLE` |
| `BILLING_SUBSCRIPTIONS` | Unauthorized charges & refund requests | 20 | 10.0% | `ESCALATE` |
| `GENERAL_PRODUCT_INQUIRY` | How-to guidance, compatibility & stores | 20 | 10.0% | `AUTO_HANDLE` |
| `AUDIO_SOUND_ISSUES` | Microphone, speaker crackle & earpiece | 18 | 9.0% | `AUTO_HANDLE` |
| `ICLOUD_STORAGE_SYNC` | iCloud storage full alerts & photo sync | 16 | 8.0% | `AUTO_HANDLE` |
| **Total** | — | **200** | **100.0%** | — |

### B. Routing Decision Breakdown:
* **`AUTO_HANDLE`**: `140` examples (**`70.0%`**)
* **`ESCALATE`**: `60` examples (**`30.0%`**)

### C. Difficulty Tier Distribution:
* **`EASY`**: `101` examples (**`50.5%`**) — Single unambiguous diagnostic symptom.
* **`MEDIUM`**: `60` examples (**`30.0%`**) — Typos, longer descriptions, or financial/security boundary decisions.
* **`HARD`**: `39` examples (**`19.5%`**) — Multi-intent messages or ambiguous contextual references.

### D. Edge Cases & Ambiguity:
* **Ambiguous Inquiries**: `39` examples (incorporates deictic references, image URLs, or context-light inquiries).
* **Multi-Intent Inquiries**: `33` examples (explicitly spans two or more diagnostic domains, e.g. battery drain + iOS update).
* **Missing Values**: `0` across all 10 schema columns.
* **Duplicate Conversation IDs**: `0` (100% unique primary keys).

---

## 5. Record Schema Definition

Every record in `data/golden/golden_set.csv` conforms to the following 10 fields:

| Field Name | Type | Description |
|---|---|---|
| `id` | `int` | Sequential integer index (1 to 200). |
| `conversation_id` | `int` | Original customer `tweet_id` linking to raw data. |
| `customer_message` | `string` | Unescaped, cleaned customer inquiry text. |
| `conversation_context` | `string` | Parent tweet message if part of an ongoing thread; `"N/A"` if starter. |
| `intent` | `string` | Candidate intent tag awaiting human verification. |
| `expected_decision` | `string` | Routing classification: `AUTO_HANDLE` or `ESCALATE`. |
| `expected_escalation_reason` | `string` | Explicit rationale explaining why human intervention is required. |
| `reference_reply` | `string` | Gold-standard customer response for text evaluation. |
| `difficulty` | `string` | Categorical complexity: `EASY`, `MEDIUM`, or `HARD`. |
| `annotation_notes` | `string` | Auditor notes detailing multi-intent conflicts or context ambiguity. |

---

## 6. Human Reviewer Workflow & CLI Tooling

To ensure the golden dataset is genuinely human-labelled rather than an unreviewed algorithmic output, an interactive CLI tool is provided:

```bash
# Launch the interactive review workflow
python scripts/label_golden_set.py
```

### Reviewer Workflow Capabilities:
* **Inspect Context**: View customer message, conversation history, and proposed labels.
* **Confirm / Advance**: Press `[Enter]` to confirm current values and move to the next record.
* **Change Intent**: Type `1`–`10` to immediately reassign to another category.
* **Toggle Decision**: Type `d` to toggle between `AUTO_HANDLE` and `ESCALATE`.
* **Edit Reference Reply**: Type `reply <new text>` to update the reference response.
* **Update Escalation Reason**: Type `reason <new text>` to supply bespoke rationale.
* **Jump to Record**: Type `jump <id>` to review a specific item.
* **Save & Exit**: Type `q` at any point; progress is automatically saved to `data/golden/golden_set.csv`.

---

*Status: Stratified sample generated and validated; awaiting human annotation verification.*
