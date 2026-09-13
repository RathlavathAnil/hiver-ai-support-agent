package com.hiver.supportagent.service;

import com.hiver.supportagent.model.EscalationDecision;

/**
 * Decides whether a customer message should be auto-handled by the AI
 * or escalated to a human agent, with an explicit reason.
 */
public interface EscalationService {

    /**
     * Determine escalation decision for a customer message.
     *
     * @param customerMessage the raw customer message
     * @param intent the classified intent
     * @param confidence the intent classification confidence
     * @param similarConversations historical conversations for context
     * @return escalation decision with reason
     */
    EscalationDecision decide(String customerMessage, String intent, double confidence,
                              java.util.List<com.hiver.supportagent.model.AgentResponse.SimilarConversation> similarConversations);
}
