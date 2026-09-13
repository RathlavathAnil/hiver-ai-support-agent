package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

class ConversationRetrieverTest {

    private EntityManager entityManager;
    private EmbeddingService embeddingService;
    private ConversationRetrieverImpl retriever;

    @BeforeEach
    void setUp() {
        entityManager = mock(EntityManager.class);
        embeddingService = new DeterministicFallbackEmbeddingService();
        retriever = new ConversationRetrieverImpl(entityManager, embeddingService);
    }

    @Test
    @DisplayName("Empty or null input returns empty list without querying database")
    void findSimilar_EmptyMessageReturnsEmpty() {
        List<SimilarConversation> res1 = retriever.findSimilar("", 3);
        List<SimilarConversation> res2 = retriever.findSimilar(null, 3);

        assertTrue(res1.isEmpty());
        assertTrue(res2.isEmpty());
        verifyNoInteractions(entityManager);
    }

    @Test
    @DisplayName("Similarity threshold filters out low-similarity results")
    void findSimilar_AppliesSimilarityThreshold() {
        Query mockQuery = mock(Query.class);
        when(entityManager.createNativeQuery(anyString())).thenReturn(mockQuery);
        when(mockQuery.setParameter(anyString(), any())).thenReturn(mockQuery);

        // Return 2 rows: one above 0.35 threshold (0.82) and one below (0.20)
        List<Object[]> mockRows = List.of(
                new Object[]{"My screen is cracked", "Please visit Genius Bar", "HARDWARE_PHYSICAL_DAMAGE", 0.82},
                new Object[]{"How to make a call?", "Open phone app", "GENERAL_PRODUCT_INQUIRY", 0.20}
        );
        when(mockQuery.getResultList()).thenReturn(mockRows);

        List<SimilarConversation> results = retriever.findSimilar("Broken screen on my phone", 3);

        assertEquals(1, results.size(), "Only result above similarity threshold should be returned");
        assertEquals("HARDWARE_PHYSICAL_DAMAGE", results.get(0).intent());
        assertEquals(0.82, results.get(0).similarityScore(), 1e-4);
    }
}
