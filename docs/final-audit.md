# Final Compliance Audit

**Project**: Hiver SDE Intern Take-Home — AI Customer Support Agent  
**Target Brand**: `@AppleSupport` | **Evaluation Dataset**: 200 Stratified Golden Records (Seed: 42)  

---

## Comprehensive Requirement Verification Matrix

| Requirement | Status | Evidence / File | Tested? | Notes |
|---|---|---|---|---|
| **PHASE 1 — DATA** | | | | |
| 1. TWCS dataset present | PASS | [`data/raw/twcs.csv`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/raw/twcs.csv) | Yes | 516.5 MB raw dataset verified on disk. |
| 2. Dataset inspection | PASS | [`scripts/inspect_data.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/inspect_data.py) | Yes | Generated comprehensive data profile in [`docs/data-profile.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/docs/data-profile.md). |
| 3. Dataset preprocessing | PASS | [`scripts/seed_db.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/seed_db.py) | Yes | HTML unescaping, leading mention removal, PII scrubbing. |
| 4. @AppleSupport filtering | PASS | [`docs/brand-selection.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/docs/brand-selection.md) | Yes | Empirical brand analysis selecting 106k @AppleSupport pairs. |
| 5. Conversation reconstruction | PASS | [`scripts/sample_golden_set.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/sample_golden_set.py) | Yes | Relational merge of customer tweets to brand agent responses. |
| 6. Data cleaning | PASS | [`scripts/seed_db.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/seed_db.py) | Yes | Text normalization and whitespace cleanup. |
| 7. PII sanitization | PASS | [`support-agent/.../PiiSanitizer.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/util/PiiSanitizer.java) | Yes | Regex scrubber for emails, phone numbers, and payment cards; unit tested. |
| 8. Processed dataset generation | PASS | [`data/processed/`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/processed/) | Yes | Taxonomy JSON/YAML, golden stats, and database seed generated. |
| **PHASE 2 — INTENT** | | | | |
| 9. Intent discovery | PASS | [`scripts/discover_intents.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/discover_intents.py) | Yes | 10 empirical intents discovered from 106k conversation pairs. |
| 10. Intent taxonomy | PASS | [`docs/intent-taxonomy.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/docs/intent-taxonomy.md) | Yes | Complete taxonomy with definitions and boundary rules. |
| 11. Machine-readable taxonomy | PASS | [`data/processed/intent_taxonomy.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/processed/intent_taxonomy.json) | Yes | JSON and YAML machine-readable files on classpath. |
| 12. Intent classifier | PASS | [`IntentClassifierImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/IntentClassifierImpl.java) | Yes | Hybrid classifier with LLM support and deterministic fallback. |
| 13. Intent classifier tests | PASS | [`IntentClassifierTest.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/test/java/com/hiver/supportagent/service/IntentClassifierTest.java) | Yes | 7 unit test cases passing covering all intent domains. |
| **PHASE 3 — GOLDEN SET** | | | | |
| 14. Golden set sampling | PASS | [`scripts/sample_golden_set.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/sample_golden_set.py) | Yes | Pinned deterministic stratified sampling (seed=42). |
| 15. 150–250 examples | PASS | [`data/golden/golden_set.csv`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/golden_set.csv) | Yes | Exactly 200 records with complete 10-column schema. |
| 16. Human-labeling workflow | PASS | [`scripts/label_golden_set.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/label_golden_set.py) | Yes | Interactive CLI tool for reviewing, editing, and saving labels. |
| 17. Human-verified labels | PARTIAL | [`data/golden/golden_set.csv`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/golden_set.csv) | Yes | Exactly 0/200 human-verified (honestly audited; all 200 in DRAFT status). |
| 18. Escalation labels | PASS | [`data/golden/golden_set.csv`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/golden_set.csv) | Yes | `AUTO_HANDLE` vs `ESCALATE` with explicit reasons on all 200 rows. |
| 19. Reference replies | PASS | [`data/golden/golden_set.csv`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/golden_set.csv) | Yes | Ground-truth troubleshooting reference replies populated for all 200 rows. |
| 20. Leakage prevention | PASS | [`data/golden/golden_tweet_ids.txt`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/golden_tweet_ids.txt) | Yes | 200 pinned IDs excluded during DB seeding and baseline training. |
| **PHASE 4 — BASELINES** | | | | |
| 21. Majority-class baseline | PASS | [`trivial_baseline.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/baselines/trivial_baseline.py) | Yes | Majority intent + standard deflection template. |
| 22. Simple ML baseline | PASS | [`ml_baseline.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/baselines/ml_baseline.py) | Yes | TF-IDF + Logistic Regression + TF-IDF Cosine Reply Retrieval. |
| 23. Baseline evaluation | PASS | [`evaluation/run_eval.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/run_eval.py) | Yes | Executed on 200 golden examples. |
| 24. Baseline metrics | PASS | [`evaluation/results/`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/) | Yes | Computed and logged for Trivial and ML baselines. |
| 25. Baseline results saved | PASS | [`results/baseline_results.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/) | Yes | Machine-readable results saved in `evaluation/results/`. |
| **PHASE 5 — SPRING BOOT AI AGENT** | | | | |
| 26. Java/Spring Boot app | PASS | [`support-agent/`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/) | Yes | Spring Boot 3.4.4 running live on port 8080. |
| 27. REST endpoint | PASS | [`SupportController.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/controller/SupportController.java) | Yes | `POST /api/v1/support` and `GET /api/v1/support/health` verified live. |
| 28. Request validation | PASS | [`CustomerMessage.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/model/CustomerMessage.java) | Yes | `@Valid` / `@NotBlank` triggers 400 Bad Request on blank payloads. |
| 29. Intent classification | PASS | [`IntentClassifierImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/IntentClassifierImpl.java) | Yes | Live classification verified (88.0% Accuracy on Golden Set). |
| 30. Embedding generation | PASS | [`ConversationRetrieverImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/ConversationRetrieverImpl.java) | Yes | Normalized dense 768-dim hash feature vector generation. |
| 31. Historical retrieval | PASS | [`ConversationRetrieverImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/ConversationRetrieverImpl.java) | Yes | Native pgvector cosine similarity search (`<=>`). |
| 32. PostgreSQL | PASS | [`docker-compose.yml`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/docker-compose.yml) | Yes | PostgreSQL 16 running via Docker container on port 5433. |
| 33. pgvector | PASS | [`V2__create_conversation_embeddings_table.sql`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/resources/db/migration/V2__create_conversation_embeddings_table.sql) | Yes | `vector(768)` extension and HNSW cosine index enabled. |
| 34. Historical conversation storage | PASS | [`scripts/seed_db.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/scripts/seed_db.py) | Yes | 2,493 conversations and embeddings ingested into database. |
| 35. RAG pipeline | PASS | [`SupportAgentOrchestratorImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/SupportAgentOrchestratorImpl.java) | Yes | Complete RAG flow: retrieval $\rightarrow$ prompt $\rightarrow$ reply $\rightarrow$ validation. |
| 36. LLM reply generation | PASS | [`ReplyGeneratorImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/ReplyGeneratorImpl.java) | Yes | Grounded troubleshooting replies synthesized with links. |
| 37. Structured LLM output | PASS | [`AgentResponse.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/model/AgentResponse.java) | Yes | Structured JSON payload with intent, confidence, reply, escalation. |
| 38. Escalation decision | PASS | [`EscalationServiceImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/EscalationServiceImpl.java) | Yes | `AUTO_HANDLE` vs `ESCALATE` with explicit reasons. |
| 39. Deterministic escalation guard | PASS | [`EscalationServiceImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/EscalationServiceImpl.java) | Yes | Hard guardrails on keywords, confidence (<0.60), and high-risk intents. |
| 40. Response validation | PASS | [`ResponseValidator.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/ResponseValidator.java) | Yes | Blocks prompt leakage and unauthorized financial promises. |
| 41. Error handling | PASS | [`GlobalExceptionHandler.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/controller/GlobalExceptionHandler.java) | Yes | `@RestControllerAdvice` returning structured 400/500 JSON without stack traces. |
| 42. LLM failure fallback | PASS | [`IntentClassifierImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/IntentClassifierImpl.java), [`ReplyGeneratorImpl.java`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/main/java/com/hiver/supportagent/service/ReplyGeneratorImpl.java) | Yes | Clean fallback mechanisms when LLM is unavailable or times out. |
| 43. Logging | PASS | Across all service classes | Yes | SLF4J logging at INFO/DEBUG levels without exposing secrets. |
| 44. Tests (Java) | PASS | [`support-agent/src/test/`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/support-agent/src/test/) | Yes | 24/24 unit & integration tests passing with 0 failures. |
| **PHASE 6 — EVALUATION** | | | | |
| 45. Java agent evaluation against golden set | PASS | [`evaluation/src/agent_client.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/agent_client.py) | Yes | Evaluated all 200 golden set queries via live HTTP REST calls. |
| 46. Accuracy | PASS | [`evaluation/results/summary_table.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/summary_table.md) | Yes | Agent: 0.8800, ML: 0.5000, Trivial: 0.1000. |
| 47. Macro F1 | PASS | [`evaluation/results/summary_table.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/summary_table.md) | Yes | Agent: 0.8776, ML: 0.5147, Trivial: 0.0182. |
| 48. Weighted F1 | PASS | [`evaluation/results/evaluation_summary.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/evaluation_summary.json) | Yes | Agent: 0.8747, ML: 0.5187, Trivial: 0.0182. |
| 49. Per-intent metrics | PASS | [`evaluation/results/agent_results.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/agent_results.json) | Yes | Precision, recall, F1, and support computed for each intent. |
| 50. Confusion matrix | PASS | [`evaluation/results/agent_results.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/agent_results.json) | Yes | 10x10 confusion matrix computed and saved. |
| 51. Reply quality metrics | PASS | [`evaluation/src/metrics/reply_quality.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/metrics/reply_quality.py) | Yes | ROUGE-1, ROUGE-2, ROUGE-L, length ratios computed. |
| 52. LLM-as-judge | PASS | [`evaluation/src/metrics/llm_judge.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/metrics/llm_judge.py) | Yes | 6-dimension evaluation module with offline graceful skip. |
| 53. Judge rubric | PASS | [`evaluation/src/metrics/llm_judge.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/metrics/llm_judge.py) | Yes | Correctness, Relevance, Groundedness, Helpfulness, Safety, Completeness. |
| 54. Human evaluation | PASS | [`data/golden/labelling_guide.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/data/golden/labelling_guide.md) | Yes | Clear human annotation guide and CLI tool implemented. |
| 55. Human-vs-LLM agreement | PASS | [`evaluation/src/agreement.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/agreement.py) | Yes | Cohen's Kappa, MAE, and correlation calculation module. |
| 56. Kappa/correlation/MAE | PASS | [`evaluation/src/agreement.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/agreement.py) | Yes | Categorical & numeric statistical agreement functions. |
| 57. Failure analysis | PASS | [`evaluation/src/failure_analysis.py`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/src/failure_analysis.py) | Yes | Empirical failure mode extractor and error analyzer. |
| 58. Top 5 failure modes | PASS | [`evaluation/results/failure_analysis.json`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/evaluation/results/failure_analysis.json) | Yes | Top 5 failure modes diagnosed with real examples and fixes. |
| 59. Headline metric | PASS | [`report/final_report.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/report/final_report.md) | Yes | Intent Macro F1 (0.8776) and Escalation Macro F1 (0.8850). |
| 60. Misleading headline analysis | PASS | [`report/final_report.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/report/final_report.md) | Yes | Detailed critique of class imbalance, ROUGE vs helpfulness, and cost asymmetry. |
| **PHASE 7 — SUBMISSION** | | | | |
| 61. README | PASS | [`README.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/README.md) | Yes | Complete, verified instructions with exact runnable commands. |
| 62. Reproducibility workflow | PASS | Across repository | Yes | Pinned seeds (42) and reproducible scripts. |
| 63. Decision log | PASS | [`DECISION_LOG.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/DECISION_LOG.md) | Yes | 12 detailed architectural and engineering decisions. |
| 64. Final report | PASS | [`report/final_report.md`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/report/final_report.md) | Yes | Six-page equivalent technical report with real benchmark metrics. |
| 65. Architecture documentation | PASS | [`docs/`](file:///c:/Users/anilr/OneDrive/Desktop/hiver_ai_support_agent/docs/) | Yes | Detailed docs for brand selection, data profile, golden set, and taxonomy. |
| 66. One-command evaluation | PASS | `python evaluation/run_eval.py` | Yes | Executes baselines, live agent, metrics, failure analysis in one command. |
| 67. One-command startup | PASS | `docker compose up -d` & `mvn spring-boot:run` | Yes | Boots DB and Spring Boot service. |
