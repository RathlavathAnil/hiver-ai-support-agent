package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

/**
 * Genuine semantic embedding service powered by Google Gemini API (gemini-embedding-001).
 * Generates high-quality 768-dimensional dense semantic vector representations for pgvector.
 *
 * Configured with taskType='RETRIEVAL_QUERY' for online customer message inference
 * and explicit outputDimensionality=768.
 */
public class GeminiEmbeddingService implements EmbeddingService {

    private static final Logger log = LoggerFactory.getLogger(GeminiEmbeddingService.class);
    private static final int DIMENSION = 768;

    private final String apiKey;
    private final String modelName;
    private final String baseUrl;
    private final String taskType;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public GeminiEmbeddingService(
            String apiKey,
            String modelName,
            String baseUrl,
            String taskType,
            ObjectMapper objectMapper
    ) {
        if (apiKey == null || apiKey.trim().isBlank()) {
            throw new IllegalArgumentException("[EMBEDDING] GEMINI_API_KEY must be provided when using GeminiEmbeddingService.");
        }
        this.apiKey = apiKey.trim();
        this.modelName = (modelName != null && !modelName.isBlank()) ? modelName.trim() : "gemini-embedding-001";
        this.baseUrl = (baseUrl != null && !baseUrl.isBlank())
                ? baseUrl.trim()
                : "https://generativelanguage.googleapis.com/v1beta/models";
        this.taskType = (taskType != null && !taskType.isBlank()) ? taskType.trim() : "RETRIEVAL_QUERY";
        this.objectMapper = objectMapper != null ? objectMapper : new ObjectMapper();
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        log.info("[EMBEDDING] Initialized GeminiEmbeddingService: model='{}', taskType='{}', dim={}",
                this.modelName, this.taskType, DIMENSION);
    }

    public GeminiEmbeddingService(
            String apiKey,
            String modelName,
            String baseUrl,
            ObjectMapper objectMapper
    ) {
        this(apiKey, modelName, baseUrl, "RETRIEVAL_QUERY", objectMapper);
    }

    @Override
    public float[] embed(String text) {
        if (text == null || text.isBlank()) {
            return new float[DIMENSION];
        }

        try {
            String endpoint = String.format("%s/%s:embedContent?key=%s", baseUrl, modelName, apiKey);

            Map<String, Object> requestBody = Map.of(
                    "model", "models/" + modelName,
                    "content", Map.of(
                            "parts", java.util.List.of(
                                    Map.of("text", text)
                            )
                    ),
                    "taskType", taskType,
                    "outputDimensionality", DIMENSION
            );

            String requestJson = objectMapper.writeValueAsString(requestBody);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(endpoint))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(requestJson))
                    .build();

            long start = System.currentTimeMillis();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            long elapsed = System.currentTimeMillis() - start;

            if (response.statusCode() == 200) {
                JsonNode root = objectMapper.readTree(response.body());
                JsonNode valuesNode = root.path("embedding").path("values");

                if (valuesNode.isArray() && valuesNode.size() > 0) {
                    if (valuesNode.size() != DIMENSION) {
                        throw new IllegalStateException(String.format(
                                "Expected embedding dimension %d, but Gemini returned %d", DIMENSION, valuesNode.size()));
                    }

                    float[] embedding = new float[DIMENSION];
                    double sumSq = 0.0;
                    for (int i = 0; i < DIMENSION; i++) {
                        embedding[i] = (float) valuesNode.get(i).asDouble();
                        sumSq += embedding[i] * embedding[i];
                    }

                    // Ensure unit L2 normalization
                    double norm = Math.sqrt(sumSq);
                    if (norm > 1e-6) {
                        for (int i = 0; i < DIMENSION; i++) {
                            embedding[i] = (float) (embedding[i] / norm);
                        }
                    }

                    log.debug("[EMBEDDING] Generated Gemini semantic embedding via '{}' (dim={}, elapsed={}ms)",
                            modelName, embedding.length, elapsed);
                    return embedding;
                }
            }

            // Loud failure on non-200 status code
            String errorDetails = sanitizeErrorMessage(response.body());
            String errorMsg = String.format("[EMBEDDING] Gemini API failed with HTTP status %d: %s",
                    response.statusCode(), errorDetails);
            log.error(errorMsg);
            throw new RuntimeException(errorMsg);

        } catch (RuntimeException re) {
            throw re;
        } catch (Exception e) {
            String errorMsg = "[EMBEDDING] Gemini embedding call failed: " + e.getMessage();
            log.error(errorMsg, e);
            throw new RuntimeException(errorMsg, e);
        }
    }

    @Override
    public int getDimension() {
        return DIMENSION;
    }

    @Override
    public String getProviderName() {
        return "gemini-" + modelName;
    }

    @Override
    public boolean isSemantic() {
        return true;
    }

    private String sanitizeErrorMessage(String body) {
        if (body == null) return "null";
        // Strip out any sensitive tokens if present
        String sanitized = body.replaceAll("key=[A-Za-z0-9_-]+", "key=REDACTED");
        if (sanitized.length() > 300) return sanitized.substring(0, 300) + "...";
        return sanitized;
    }
}
