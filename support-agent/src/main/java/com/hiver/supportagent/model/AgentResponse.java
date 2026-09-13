package com.hiver.supportagent.model;

/**
 * Represents the AI agent's complete response to a customer message.
 * Encapsulates intent classification, draft reply, and escalation decision.
 */
public record AgentResponse(
        String intent,
        double confidence,
        String reply,
        EscalationDecision escalation,
        java.util.List<SimilarConversation> similarConversations
) {

    /**
     * A similar historical conversation retrieved via vector search.
     */
    public record SimilarConversation(
            String customerText,
            String agentReply,
            String intent,
            double similarityScore
    ) {}
}
