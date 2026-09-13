package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse;
import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.service.IntentClassifier.IntentResult;
import com.hiver.supportagent.util.PiiSanitizer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Concrete orchestrator coordinating the end-to-end AI support agent pipeline.
 */
@Service
public class SupportAgentOrchestratorImpl implements SupportAgentOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(SupportAgentOrchestratorImpl.class);

    private final PiiSanitizer piiSanitizer;
    private final ConversationRetriever conversationRetriever;
    private final IntentClassifier intentClassifier;
    private final ReplyGenerator replyGenerator;
    private final EscalationService escalationService;
    private final ResponseValidator responseValidator;

    public SupportAgentOrchestratorImpl(
            PiiSanitizer piiSanitizer,
            ConversationRetriever conversationRetriever,
            IntentClassifier intentClassifier,
            ReplyGenerator replyGenerator,
            EscalationService escalationService,
            ResponseValidator responseValidator
    ) {
        this.piiSanitizer = piiSanitizer;
        this.conversationRetriever = conversationRetriever;
        this.intentClassifier = intentClassifier;
        this.replyGenerator = replyGenerator;
        this.escalationService = escalationService;
        this.responseValidator = responseValidator;
    }

    @Override
    public AgentResponse processMessage(String customerMessage) {
        log.info("Processing customer support message: '{}'", customerMessage);

        // 1. PII Sanitization
        String sanitizedMessage = piiSanitizer.sanitize(customerMessage);

        // 2. Historical pgvector Retrieval
        List<SimilarConversation> similarConversations = conversationRetriever.findSimilar(sanitizedMessage, 3);
        log.debug("Found {} historical conversations", similarConversations.size());

        // 3. Intent Classification
        IntentResult intentResult = intentClassifier.classify(sanitizedMessage, similarConversations);
        log.debug("Classified Intent: {} (confidence: {})", intentResult.intent(), intentResult.confidence());

        // 4. Grounded Reply Generation
        String rawReply = replyGenerator.generateReply(sanitizedMessage, intentResult.intent(), similarConversations);

        // 5. Hybrid Escalation Decision
        EscalationDecision escalation = escalationService.decide(
                sanitizedMessage,
                intentResult.intent(),
                intentResult.confidence(),
                similarConversations
        );
        log.debug("Escalation Decision: {} - Reason: {}", escalation.decision(), escalation.reason());

        // 6. Response Validation & Safety Guardrails
        String validatedReply = responseValidator.validateAndSanitize(rawReply, sanitizedMessage, escalation);

        // 7. Assemble Structured Response
        return new AgentResponse(
                intentResult.intent(),
                intentResult.confidence(),
                validatedReply,
                escalation,
                similarConversations
        );
    }
}
