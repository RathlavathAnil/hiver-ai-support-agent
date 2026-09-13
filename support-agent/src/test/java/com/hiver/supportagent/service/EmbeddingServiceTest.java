package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class EmbeddingServiceTest {

    @Test
    @DisplayName("DeterministicFallbackEmbeddingService generates 768-dim normalized vectors")
    void fallbackEmbeddingService_GeneratesCorrectDimensions() {
        DeterministicFallbackEmbeddingService service = new DeterministicFallbackEmbeddingService();

        assertEquals(768, service.getDimension());
        assertEquals("fallback-deterministic-hash-768", service.getProviderName());
        assertFalse(service.isSemantic(), "Fallback provider must be marked non-semantic");

        float[] vector = service.embed("My battery dies very quickly on iOS 11");
        assertNotNull(vector);
        assertEquals(768, vector.length);

        // Verify L2 normalization
        double sumSq = 0.0;
        for (float v : vector) {
            sumSq += v * v;
        }
        assertEquals(1.0, Math.sqrt(sumSq), 1e-4, "Vector must be unit L2 normalized");
    }

    @Test
    @DisplayName("DeterministicFallbackEmbeddingService produces deterministic outputs for identical text")
    void fallbackEmbeddingService_IsDeterministic() {
        DeterministicFallbackEmbeddingService service = new DeterministicFallbackEmbeddingService();

        float[] vec1 = service.embed("How do I update to iOS 11?");
        float[] vec2 = service.embed("How do I update to iOS 11?");

        assertArrayEquals(vec1, vec2, "Identical input must produce identical embeddings");
    }

    @Test
    @DisplayName("GeminiEmbeddingService fails loudly when instantiated without an API key")
    void geminiEmbeddingService_ThrowsExceptionWhenKeyMissing() {
        assertThrows(IllegalArgumentException.class, () -> {
            new GeminiEmbeddingService(
                    "",
                    "gemini-embedding-001",
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    "RETRIEVAL_QUERY",
                    new ObjectMapper()
            );
        }, "Gemini service must fail loudly when no API key is provided");
    }

    @Test
    @DisplayName("GeminiEmbeddingService correctly sets model name, dimension 768, and semantic flag")
    void geminiEmbeddingService_CorrectModelMetadata() {
        GeminiEmbeddingService service = new GeminiEmbeddingService(
                "mock-api-key-12345",
                "gemini-embedding-001",
                "https://generativelanguage.googleapis.com/v1beta/models",
                "RETRIEVAL_QUERY",
                new ObjectMapper()
        );

        assertEquals(768, service.getDimension());
        assertEquals("gemini-gemini-embedding-001", service.getProviderName());
        assertTrue(service.isSemantic(), "Gemini provider must be marked semantic");
    }
}
