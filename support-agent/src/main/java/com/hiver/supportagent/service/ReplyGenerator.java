package com.hiver.supportagent.service;

/**
 * Generates brand-grounded replies to customer messages.
 * Uses historical reply patterns as grounding context.
 */
public interface ReplyGenerator {

    /**
     * Generate a draft reply grounded in historical brand responses.
     *
     * @param customerMessage the raw customer message
     * @param intent the classified intent
     * @param similarConversations historical conversations for grounding
     * @return generated reply text
     */
    String generateReply(String customerMessage, String intent,
                         java.util.List<com.hiver.supportagent.model.AgentResponse.SimilarConversation> similarConversations);
}
