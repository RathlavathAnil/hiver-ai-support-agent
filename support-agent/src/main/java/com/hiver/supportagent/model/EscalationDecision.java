package com.hiver.supportagent.model;

/**
 * Represents the escalation decision: whether a message should be
 * auto-handled by the AI or escalated to a human agent.
 */
public record EscalationDecision(
        Decision decision,
        String reason
) {

    public enum Decision {
        AUTO_HANDLE,
        ESCALATE
    }
}
