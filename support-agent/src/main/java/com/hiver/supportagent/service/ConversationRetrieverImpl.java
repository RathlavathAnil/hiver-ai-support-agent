package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Historical conversation retriever powered by pgvector and dense vector embeddings.
 * Queries PostgreSQL pgvector embeddings using cosine similarity distance (<=>).
 */
@Service
public class ConversationRetrieverImpl implements ConversationRetriever {

    private static final Logger log = LoggerFactory.getLogger(ConversationRetrieverImpl.class);

    private final EntityManager entityManager;
    private final EmbeddingService embeddingService;

    @Value("${app.retrieval.top-k:3}")
    private int defaultTopK = 3;

    @Value("${app.retrieval.similarity-threshold:0.35}")
    private double similarityThreshold = 0.35;

    @Value("${app.brand:AppleSupport}")
    private String brand = "AppleSupport";

    public ConversationRetrieverImpl(EntityManager entityManager, EmbeddingService embeddingService) {
        this.entityManager = entityManager;
        this.embeddingService = embeddingService;
        log.info("[RETRIEVER] Initialized with provider='{}' (semantic={}), topK={}, threshold={}",
                embeddingService.getProviderName(), embeddingService.isSemantic(), defaultTopK, similarityThreshold);
    }

    @Override
    public List<SimilarConversation> findSimilar(String customerMessage, int topK) {
        if (customerMessage == null || customerMessage.isBlank()) {
            return Collections.emptyList();
        }

        int limit = topK > 0 ? topK : defaultTopK;

        try {
            float[] queryEmbedding = embeddingService.embed(customerMessage);
            String vectorStr = formatVectorLiteral(queryEmbedding);

            // Native SQL query utilizing pgvector cosine distance operator (<=>)
            String sql = String.format(java.util.Locale.US, """
                SELECT c.customer_text, c.agent_reply, c.intent,
                       (1.0 - (ce.embedding <=> CAST('%s' AS vector))) AS similarity
                FROM conversations c
                JOIN conversation_embeddings ce ON c.id = ce.conversation_id
                WHERE c.brand = :brand
                ORDER BY ce.embedding <=> CAST('%s' AS vector)
            """, vectorStr, vectorStr);

            Query query = entityManager.createNativeQuery(sql);
            query.setParameter("brand", brand);
            query.setMaxResults(limit);

            @SuppressWarnings("unchecked")
            List<Object[]> rows = query.getResultList();
            List<SimilarConversation> results = new ArrayList<>(rows.size());

            for (Object[] row : rows) {
                String custText = (String) row[0];
                String agentReply = (String) row[1];
                String intent = (String) row[2];
                double similarity = row[3] != null ? ((Number) row[3]).doubleValue() : 0.0;
                log.info("[RETRIEVER] Raw DB match: similarity={}, intent={}, text='{}'",
                        similarity, intent, custText != null ? (custText.length() > 40 ? custText.substring(0, 40) + "..." : custText) : "");

                // Enforce similarity threshold guardrail
                if (similarity >= similarityThreshold) {
                    results.add(new SimilarConversation(
                            custText != null ? custText : "",
                            agentReply != null ? agentReply : "",
                            intent != null ? intent : "GENERAL_PRODUCT_INQUIRY",
                            similarity
                    ));
                }
            }

            double topScore = results.isEmpty() ? 0.0 : results.get(0).similarityScore();
            log.info("[RETRIEVER] Provider '{}' retrieved {} filtered conversations (topScore={}, threshold={})",
                    embeddingService.getProviderName(), results.size(), topScore, similarityThreshold);

            return results;

        } catch (Exception e) {
            log.error("[RETRIEVER] pgvector retrieval failed with exception:", e);
            return Collections.emptyList();
        }
    }

    /**
     * Helper to format a float array as a pgvector SQL literal string '[0.1,0.2,...]'.
     */
    public static String formatVectorLiteral(float[] vector) {
        StringBuilder sb = new StringBuilder(vector.length * 10);
        sb.append("[");
        for (int i = 0; i < vector.length; i++) {
            if (i > 0) sb.append(",");
            sb.append(String.format(java.util.Locale.US, "%.6f", vector[i]));
        }
        sb.append("]");
        return sb.toString();
    }

    /**
     * Backward-compatible static helper for computing deterministic hash embeddings.
     */
    public static float[] computeDenseEmbedding(String text, int dim) {
        return new DeterministicFallbackEmbeddingService().embed(text);
    }
}
