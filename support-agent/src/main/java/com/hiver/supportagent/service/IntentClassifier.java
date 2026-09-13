package com.hiver.supportagent.service;

/**
 * Classifies customer messages into a predefined intent taxonomy.
 * Uses RAG (retrieved similar conversations) + LLM for classification.
 */
public interface IntentClassifier {

    /**
     * Classify the intent of a customer message.
     *
     * @param customerMessage the raw customer message
     * @param similarConversations context from similar historical conversations
     * @return classification result with intent label and confidence
     */
    IntentResult classify(String customerMessage,
                          java.util.List<com.hiver.supportagent.model.AgentResponse.SimilarConversation> similarConversations);

    record IntentResult(String intent, double confidence) {}
}
