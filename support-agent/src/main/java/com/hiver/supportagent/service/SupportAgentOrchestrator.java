package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse;

/**
 * Orchestrates the full support agent pipeline:
 * 1. Retrieve similar historical conversations
 * 2. Classify intent
 * 3. Generate reply
 * 4. Decide escalation
 */
public interface SupportAgentOrchestrator {

    /**
     * Process a customer message through the full AI pipeline.
     *
     * @param customerMessage the raw customer message text
     * @return complete agent response
     */
    AgentResponse processMessage(String customerMessage);
}
