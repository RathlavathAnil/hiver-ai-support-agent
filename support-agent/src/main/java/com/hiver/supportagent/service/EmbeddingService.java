package com.hiver.supportagent.service;

/**
 * Interface for generating dense text vector embeddings for retrieval in pgvector.
 * Supports genuine semantic providers (e.g. Google Gemini) and offline fallback providers.
 */
public interface EmbeddingService {

    /**
     * Generates a dense vector embedding for the input text.
     *
     * @param text input text to embed
     * @return normalized dense vector of float values
     */
    float[] embed(String text);

    /**
     * The fixed dimension of the vector produced by this provider (e.g. 768).
     */
    int getDimension();

    /**
     * Returns the name of the active embedding provider/model.
     */
    String getProviderName();

    /**
     * Whether this service provides genuine semantic neural embeddings
     * (as opposed to offline deterministic fallback vectors).
     */
    boolean isSemantic();
}
