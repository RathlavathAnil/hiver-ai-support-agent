# Engineering Decision Log

This log records the core architectural, design, algorithmic, and data engineering decisions made for the **Hiver AI Customer Support Agent**, detailing the problem context, alternatives evaluated, technical rationale, and trade-offs.

---

## D1: Target Brand Selection — `@AppleSupport`

- **Decision**: Select `@AppleSupport` as the single target brand for building the AI support agent and evaluation harness.
- **Context & Evidence**: Empirical profiling of 2.81M tweets in the TWCS dataset showed `@AppleSupport` has 106,860 outbound brand tweets across 106,648 direct conversation pairs and 76,366 unique customers.
- **Resolution Viability**: AppleSupport demonstrates a 53.91% self-contained actionable troubleshooting resolution rate (3.7x higher than AmazonHelp at 14.58%, Uber_Support at 14.68%, and Delta at 8.08%).
- **Alternatives Considered**:
  - `@AmazonHelp`: Highest raw volume (169,840), but >85% of replies are deflections requiring private Order Management System (OMS) access unavailable to an offline AI agent.
  - `@SpotifyCares`: High cleanliness, but overly narrow domain (only 3–4 distinct intents: audio playback, offline sync, family plan).
  - `@Uber_Support`: Heavily dependent on live ride-dispatch/GPS backends for fare disputes and lost items.
  - `@Delta`: Almost 100% dependent on private GDS/PNR ticketing databases for live flight rebooking.
- **Trade-offs & Risks**: AppleSupport contains ambiguous tweets (screenshots without captions), truncated threads, noisy boilerplate, and account-specific recovery issues (activation lock, billing refunds) that require careful escalation logic.

---

## D2: Java 17 LTS & Spring Boot 3.4 Stack

- **Decision**: Build the production AI support agent using Java 17 LTS and Spring Boot 3.4.
- **Alternatives Considered**:
  - Java 21: Offers virtual threads, but Java 17 LTS is the battle-tested enterprise standard with full LTS support across all cloud environments and dependencies.
  - Python FastAPI / Flask: Faster prototyping, but the assignment specifies building a robust Spring Boot production backend.
- **Rationale**: Java 17 provides modern features (records, sealed classes, pattern matching, text blocks) that make domain models clean and concise while ensuring compatibility with Spring Boot 3.4 and Spring AI.
- **Trade-offs**: Slightly more verbose setup than Python microframeworks, but provides type safety, validation, and production enterprise architecture.

---

## D3: Single PostgreSQL Instance with `pgvector`

- **Decision**: Use PostgreSQL 16 with the `pgvector` extension for storing both relational conversation metadata and 768-dimensional dense vector embeddings in a single database.
- **Alternatives Considered**:
  - Standalone Vector DBs (Pinecone, Weaviate, Qdrant): Adds external network hops, separate cluster management, distributed transactions, and potential consistency drift between vector records and metadata.
  - In-memory FAISS: Fast, but lacks persistence, transactional consistency, and SQL query integration.
- **Rationale**: `pgvector` allows atomic relational joins between metadata (`conversations`) and vector indexes (`conversation_embeddings`) via HNSW cosine distance (`<=>`), significantly reducing operational complexity.
- **Trade-offs**: HNSW index builds require memory tuning in high-scale enterprise environments; perfectly optimal for take-home dataset scale (thousands to hundreds of thousands of vectors).

---

## D4: Semantic Vector Retrieval (Google Gemini gemini-embedding-001 + Fallback)

- **Decision**: Implement a multi-provider vector embedding architecture supporting genuine neural semantic embeddings (Google Gemini `gemini-embedding-001`, 768 dimensions) with a deterministic fallback provider for offline development.
- **Previous Approach & Why Inadequate**: The initial prototype used deterministic SHA-256 n-gram feature hashing projected into 768 dimensions. While fast and reproducible offline, feature hashing lacks semantic understanding of synonyms, paraphrasing, and cross-lingual meaning (e.g. "my battery is draining" vs "power depletes rapidly").
- **Current Architecture**:
  - `GeminiEmbeddingService`: Calls Google Gemini's official `gemini-embedding-001` API endpoint (`taskType=RETRIEVAL_QUERY`, `outputDimensionality=768`) to generate dense 768-dim semantic representations.
  - `DeterministicFallbackEmbeddingService`: Provides deterministic 768-dim hash embeddings for offline/local development when `GEMINI_API_KEY` is not present, clearly logged as non-semantic fallback.
  - Configurable via `app.embeddings.provider=gemini|fallback`, `app.embeddings.gemini.api-key`, and `app.retrieval.similarity-threshold=0.35` (configurable up to 0.65 in semantic mode).
  - Storage & Distance: PostgreSQL `pgvector` with HNSW cosine distance operator (`<=>`).
- **Trade-offs & Rationale**: Ensures production-grade genuine semantic retrieval when API keys are configured, while maintaining 100% offline runnable testability and deterministic CI/CD builds.

---

## D5: Strict Golden Set Leakage Isolation (Tweet ID Blacklist)

- **Decision**: Implement a deterministic blacklist of all 200 golden evaluation set tweet IDs (`data/golden/golden_tweet_ids.txt`) and filter them out during database seeding and baseline training.
- **Alternatives Considered**:
  - Random split during each run: High risk of test set contamination across different evaluation runs.
  - Time-based split: Difficult due to uneven distribution of brand conversation threads across time windows.
- **Rationale**: Pre-saving the exact tweet IDs guarantees 0% data leakage across the entire lifecycle: database ingestion (`scripts/seed_db.py`), ML baseline training (`evaluation/run_eval.py`), and RAG vector searches.
- **Trade-offs**: Reduces the available training set by exactly 200 records (negligible for 106K available pairs).

---

## D6: Hybrid Intent Classification (LLM + Deterministic Regex Fallback)

- **Decision**: Implement a hybrid intent classifier that uses LLM prompting when available and automatically falls back to deterministic rule/regex heuristics without failing the request.
- **Alternatives Considered**:
  - LLM-only: Hard dependency on external network and API quotas; API timeouts crash customer requests.
  - Pure Regex-only: Brittle for complex, ambiguous language with multi-clause sentences.
- **Rationale**: Provides the best of both worlds: LLM handles nuanced phrasing when online, while deterministic heuristics guarantee <10ms response times and 100% uptime in offline or test environments.
- **Trade-offs**: Rule-based fallback requires maintaining regex patterns corresponding to the 10-intent taxonomy.

---

## D7: Multi-Tier Deterministic Escalation Policy

- **Decision**: Implement deterministic guardrails that immediately trigger escalation on high-risk keywords, low confidence scores, or high-risk intents *before* relying on LLM triage.
- **Alternatives Considered**:
  - Pure LLM Escalation Triage: Vulnerable to prompt injection, hallucinated policies, and non-deterministic false negatives on dangerous issues (fraud, legal threats).
  - Pure Keyword Escalation: Misses subtle escalation context.
- **Rationale**: High-risk situations (e.g. physical battery swelling, cracked screens, unauthorized credit card charges, legal action) must NEVER be auto-handled. Deterministic guardrails enforce safety as a hard invariant.
- **Trade-offs**: Slightly higher false-positive escalation rate on ambiguous mentions, which is the correct conservative trade-off for customer support safety.

---

## D8: Response Guardrails & PII Sanitization

- **Decision**: Sanitize incoming messages for PII (emails, phone numbers, payment card numbers, user handles) and validate generated replies against prompt leaks and unauthorized financial promises.
- **Alternatives Considered**:
  - No response validation (trusting LLM raw output): Risk of model spitting out internal prompt templates or falsely promising "$50 refund has been issued".
- **Rationale**: PII sanitization protects user privacy before logging or transmitting text to LLM backends. Response validation blocks prompt leaks (`{{...}}`, `## Guidelines`) and financial hallucinations.
- **Trade-offs**: Regex-based PII scrubber may occasionally replace non-PII numerical strings matching 16-digit patterns.

---

## D9: Stratified Golden Evaluation Set Design (200 Records)

- **Decision**: Sample exactly 200 golden evaluation records deterministically (Seed: 42) across 10 intents and 3 difficulty tiers (EASY: 50%, MEDIUM: 35%, HARD: 15%).
- **Alternatives Considered**:
  - Uniform random sampling: Over-represents common intents (`SOFTWARE_UPDATE_OS`) and yields 0 examples for rare but critical intents (`ICLOUD_STORAGE_SYNC`, `HARDWARE_PHYSICAL_DAMAGE`).
- **Rationale**: Stratified sampling ensures balanced statistical evaluation across all 10 customer support categories, including adversarial and multi-intent queries.
- **Trade-offs**: Does not match the skewed production class distribution (discussed in "What is misleading about headline metrics").

---

## D10: Multi-Metric Evaluation Framework (Macro F1 over Raw Accuracy)

- **Decision**: Select **Intent Macro F1** and **Escalation Macro F1** as primary performance indicators, alongside ROUGE-L and LLM-as-a-Judge rubrics.
- **Alternatives Considered**:
  - Raw Accuracy: Misleadingly inflated by majority classes; a trivial baseline guessing the top class achieves ~30% accuracy while having 0.05 Macro F1.
  - BLEU/ROUGE as primary metric: Lexical overlap rewards verbatim copying of generic boilerplate ("Please DM us") and penalizes semantically superior, detailed diagnostic steps.
- **Rationale**: Macro F1 treats all customer support intents equally, penalizing models that fail on critical low-volume categories.
- **Trade-offs**: Requires nuanced reporting of class imbalance in production environments.

---

## D11: 4-Dimension LLM-as-a-Judge Rubric & Human Agreement Framework

- **Decision**: Design a 4-dimension evaluation rubric (Relevance, Groundedness, Helpfulness, Safety/Escalation on a 1–5 integer scale) with structured JSON output, deterministic sampling (N=20, Seed: 42), and paired human agreement validation (`HUMAN_RATING`).
- **Rubric Dimensions**:
  1. **Relevance (1–5)**: Does the reply directly address the customer's specific issue?
  2. **Groundedness (1–5)**: Is the reply supported by retrieved historical evidence and standard Apple support guidance? Penalizes hallucinations and unsupported claims.
  3. **Helpfulness (1–5)**: Does it provide clear, actionable troubleshooting steps or legitimate navigation paths?
  4. **Safety / Escalation (1–5)**: Does it avoid unauthorized financial promises and appropriately escalate sensitive cases (billing fraud, account lockouts, physical damage)?
- **Human-Agreement Framework**:
  - Sample size: N=20 deterministically sampled golden examples (clearly documented as an empirical validation sample).
  - Metrics computed: Exact Agreement Rate, Within-1-Point Rate, Mean Absolute Difference (MAD), Pearson correlation ($r$), Spearman rank correlation ($\rho$), Quadratic Weighted Cohen's Kappa, and Binary Pass/Fail ($\ge 4.0$) Kappa.
- **Trade-offs & Rationale**: Focuses LLM judging on actionable support quality dimensions while validating judge fidelity against human expert ratings without exhausting free-tier LLM generation quotas.

---

## D12: Single REST Endpoint Architecture (`POST /api/v1/support`)

- **Decision**: Provide a unified REST endpoint returning the complete triage payload (`intent`, `confidence`, `reply`, `escalation`, `similarConversations`) in a single atomic response.
- **Alternatives Considered**:
  - Separate microservice endpoints (`/classify`, `/retrieve`, `/generate`, `/escalate`): Requires multiple round trips and client-side orchestration.
- **Rationale**: Simplifies client integration, minimizes network overhead, and guarantees atomic execution of intent classification, grounding, and escalation policies.
- **Trade-offs**: Client cannot query intent without also generating reply; mitigated by fast <15ms response latency.

---

## D13: Retrieval Corpus Subsampling (Quota-Safe Fast Initialization)

- **Decision**: Subsample the historical retrieval corpus to a quota-safe subset (e.g. 50–500 non-golden AppleSupport conversations) during database seeding.
- **Rationale & Quota Management**:
  - Gemini Free Tier limits embedding ingestion (100 RPM / 1,000 RPD).
  - Subsampling provides rich domain coverage across all 10 customer support categories while enabling fast (< 1 min), reliable, and deterministic database initialization.
- **Data Leakage Invariant**:
  - All 200 golden evaluation set tweet IDs (`data/golden/golden_tweet_ids.txt`) remain strictly excluded from the retrieval corpus, ensuring 0% evaluation contamination.
- **Trade-offs**:
  - Smaller retrieval corpora represent a subset rather than the entire 106K historical tweet corpus. This constraint and its impact on RAG retrieval are transparently documented as a limitation and addressed in the "One More Week" expansion plan.


