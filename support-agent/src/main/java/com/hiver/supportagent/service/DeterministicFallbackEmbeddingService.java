package com.hiver.supportagent.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Deterministic hash-based embedding service for offline/local development and unit testing
 * when no external semantic embedding API key (such as GEMINI_API_KEY) is configured.
 *
 * NOTE: This is NOT a semantic embedding model. It provides deterministic 768-dimensional
 * vectors to keep the application and database pipeline functional offline without external APIs.
 */
public class DeterministicFallbackEmbeddingService implements EmbeddingService {

    private static final Logger log = LoggerFactory.getLogger(DeterministicFallbackEmbeddingService.class);
    private static final int DIMENSION = 768;

    public DeterministicFallbackEmbeddingService() {
        log.warn("================================================================================");
        log.warn("[NOTICE] Active Embedding Provider: DeterministicFallbackEmbeddingService");
        log.warn("[NOTICE] Running with offline hash vectors (dim={}) for local development.", DIMENSION);
        log.warn("[NOTICE] For genuine semantic embeddings, set GEMINI_API_KEY and app.embeddings.provider=gemini");
        log.warn("================================================================================");
    }

    @Override
    public float[] embed(String text) {
        float[] vec = new float[DIMENSION];
        if (text == null || text.isBlank()) {
            vec[0] = 1.0f;
            return vec;
        }

        String[] words = text.toLowerCase().trim().split("\\s+");
        List<String> features = new ArrayList<>();
        Collections.addAll(features, words);
        for (int i = 0; i < words.length - 1; i++) {
            features.add(words[i] + "_" + words[i + 1]);
        }

        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            BigInteger dimBig = BigInteger.valueOf(DIMENSION);
            for (String feat : features) {
                byte[] hash = digest.digest(feat.getBytes(StandardCharsets.UTF_8));
                BigInteger h = new BigInteger(1, hash);
                int idx = h.mod(dimBig).intValue();
                float sign = h.testBit(16) ? -1.0f : 1.0f;
                vec[idx] += sign;
            }
        } catch (NoSuchAlgorithmException ignored) {}

        double sumSq = 0.0;
        for (float v : vec) {
            sumSq += v * v;
        }
        double norm = Math.sqrt(sumSq);
        if (norm > 1e-6) {
            for (int i = 0; i < DIMENSION; i++) {
                vec[i] = (float) (vec[i] / norm);
            }
        } else {
            vec[0] = 1.0f;
        }
        return vec;
    }

    @Override
    public int getDimension() {
        return DIMENSION;
    }

    @Override
    public String getProviderName() {
        return "fallback-deterministic-hash-768";
    }

    @Override
    public boolean isSemantic() {
        return false;
    }
}
