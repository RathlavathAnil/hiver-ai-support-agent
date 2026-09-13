package com.hiver.supportagent.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hiver.supportagent.service.DeterministicFallbackEmbeddingService;
import com.hiver.supportagent.service.EmbeddingService;
import com.hiver.supportagent.service.GeminiEmbeddingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Spring configuration for vector embedding services.
 * Automatically selects between genuine Gemini semantic embeddings (gemini-embedding-001)
 * and local offline fallback.
 */
@Configuration
public class EmbeddingConfig {

    private static final Logger log = LoggerFactory.getLogger(EmbeddingConfig.class);

    @Value("${app.embeddings.provider:gemini}")
    private String provider;

    @Value("${app.embeddings.gemini.api-key:${GEMINI_API_KEY:}}")
    private String geminiApiKey;

    @Value("${app.embeddings.gemini.model:gemini-embedding-001}")
    private String geminiModel;

    @Value("${app.embeddings.gemini.base-url:https://generativelanguage.googleapis.com/v1beta/models}")
    private String geminiBaseUrl;

    @Bean
    public EmbeddingService embeddingService(ObjectMapper objectMapper) {
        String normalizedProvider = provider != null ? provider.trim().toLowerCase() : "gemini";

        if ("fallback".equals(normalizedProvider)) {
            log.info("[CONFIG] Embedding provider explicitly set to FALLBACK (offline mode).");
            return new DeterministicFallbackEmbeddingService();
        }

        if (geminiApiKey != null && !geminiApiKey.isBlank()) {
            log.info("[CONFIG] Embedding provider set to GEMINI with model '{}' (taskType='RETRIEVAL_QUERY', dim=768).", geminiModel);
            return new GeminiEmbeddingService(geminiApiKey, geminiModel, geminiBaseUrl, "RETRIEVAL_QUERY", objectMapper);
        } else {
            log.warn("[CONFIG] Embedding provider requested as '{}', but GEMINI_API_KEY is not configured.", provider);
            log.warn("[CONFIG] Defaulting to DeterministicFallbackEmbeddingService for offline development.");
            return new DeterministicFallbackEmbeddingService();
        }
    }
}
