# Implementation Status Audit

## Repository State Prior to Final Pass

### 1. Data & Discovery Layer
- **Dataset**: `data/raw/twcs.csv` verified present (516.5 MB, 2.81M tweets).
- **Inspection**: `scripts/inspect_data.py` executed; brand profile for `@AppleSupport` (106,648 conversation pairs) documented in `docs/brand-selection.md` and `docs/data-profile.md`.
- **Intent Discovery**: `scripts/discover_intents.py` discovered a 10-intent taxonomy, documented in `docs/intent-taxonomy.md` and serialized in `data/processed/intent_taxonomy.json` and `data/processed/intent_taxonomy.yaml`.
- **Golden Evaluation Set**: `scripts/sample_golden_set.py` deterministically sampled 200 stratified records (seed=42) to `data/golden/golden_set.csv`. Golden tweet IDs isolated in `data/golden/golden_tweet_ids.txt` to guarantee 0 data leakage.
- **Annotation Status**: All 200 golden set records were drafted via heuristic stratification; exact human verification count is 0 / 200. The interactive CLI tool `scripts/label_golden_set.py` is available for human verification.

### 2. Spring Boot Application (`support-agent/`)
- **Maven & Dependencies**: `pom.xml` configured for Java 17, Spring Boot 3.4.0, Spring AI Vertex AI Gemini, Flyway, PostgreSQL, and pgvector.
- **REST Controller**: `SupportController.java` scaffolded with `POST /api/v1/support` and `GET /api/v1/support/health`.
- **Domain Models**: `AgentResponse.java`, `CustomerMessage.java`, `EscalationDecision.java`, and `Conversation.java` defined.
- **Flyway Migrations**: `V1__create_conversations_table.sql` and `V2__create_conversation_embeddings_table.sql` configured.
- **Pending Implementations**:
  - Concrete services for `IntentClassifier`, `ConversationRetriever`, `ReplyGenerator`, `EscalationService`, and `SupportAgentOrchestrator`.
  - Response validation and deterministic safety guardrails.
  - Exception handling (`@ControllerAdvice`).
  - Unit and integration tests (`src/test/`).

### 3. Evaluation Framework (`evaluation/`)
- **Config**: `eval_config.yaml` defines taxonomy and evaluation thresholds.
- **Pending Implementations**:
  - `evaluation/src/baselines/trivial_baseline.py` (Majority class).
  - `evaluation/src/baselines/ml_baseline.py` (TF-IDF + Logistic Regression).
  - `evaluation/src/metrics/intent_metrics.py` (Accuracy, Macro/Weighted F1, Confusion Matrix).
  - `evaluation/src/metrics/reply_quality.py` (ROUGE-1, ROUGE-2, ROUGE-L).
  - `evaluation/src/metrics/llm_judge.py` (6-dimension evaluation rubric).
  - `evaluation/src/agreement.py` (Human vs LLM agreement statistics).
  - `evaluation/src/failure_analysis.py` (Top 5 empirical failure modes).
  - `evaluation/src/agent_client.py` (REST client for Spring Boot).
  - `evaluation/run_eval.py` (Unified evaluation harness).

### 4. Database & Ingestion
- **Docker Compose**: `docker-compose.yml` runs `pgvector/pgvector:pg16` on port 5432.
- **Pending Implementation**: `scripts/seed_db.py` to ingest cleaned, PII-sanitized `@AppleSupport` conversation pairs with vector embeddings and leak prevention.

---
*Status updated during the final implementation pass.*
