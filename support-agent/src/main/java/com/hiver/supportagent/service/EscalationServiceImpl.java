package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Concrete escalation decision service.
 * Hybrid system: Deterministic guardrails (keywords, confidence, intent policy) + LLM reasoning.
 */
@Service
public class EscalationServiceImpl implements EscalationService {

    private static final Logger log = LoggerFactory.getLogger(EscalationServiceImpl.class);

    @Value("${app.escalation.confidence-threshold:0.60}")
    private double confidenceThreshold;

    @Value("${app.escalation.keywords:cancel,legal,lawyer,manager,supervisor,refund,complaint,sue,fraud,hacked,stolen,unauthorized,crack,water damage,liquid}")
    private List<String> escalationKeywords;

    @Value("classpath:prompts/escalation_decision.st")
    private Resource promptResource;

    @Value("${app.brand:AppleSupport}")
    private String brand;

    private final ObjectMapper objectMapper;

    @Autowired(required = false)
    private org.springframework.ai.chat.model.ChatModel chatModel;

    public EscalationServiceImpl(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public EscalationDecision decide(String customerMessage, String intent, double confidence,
                                     List<SimilarConversation> similarConversations) {
        String lowerMsg = customerMessage != null ? customerMessage.toLowerCase() : "";

        // 1. DETERMINISTIC GUARDRAIL: High-Risk Keyword Check
        for (String kw : escalationKeywords) {
            String trimmedKw = kw.trim().toLowerCase();
            if (!trimmedKw.isBlank() && Pattern.compile("\\b" + Pattern.quote(trimmedKw) + "\\b", Pattern.CASE_INSENSITIVE).matcher(lowerMsg).find()) {
                log.info("Escalation triggered by deterministic keyword guardrail: '{}'", trimmedKw);
                return new EscalationDecision(
                        Decision.ESCALATE,
                        "Triggered deterministic high-risk keyword guardrail: '" + trimmedKw + "'"
                );
            }
        }

        // 2. DETERMINISTIC GUARDRAIL: Low Classification Confidence Check
        if (confidence < confidenceThreshold) {
            log.info("Escalation triggered by low classification confidence: {} < {}", confidence, confidenceThreshold);
            return new EscalationDecision(
                    Decision.ESCALATE,
                    String.format("Intent classification confidence (%.2f) is below automated handling threshold (%.2f)",
                            confidence, confidenceThreshold)
            );
        }

        // 3. DETERMINISTIC GUARDRAIL: High-Risk Intent Policies
        if ("HARDWARE_PHYSICAL_DAMAGE".equalsIgnoreCase(intent)) {
            return new EscalationDecision(
                    Decision.ESCALATE,
                    "Physical hardware damage requires in-person store inspection, hardware diagnostic tools, or Genius Bar repair appointment."
            );
        }
        if ("ACCOUNT_ACCESS_SECURITY".equalsIgnoreCase(intent)) {
            return new EscalationDecision(
                    Decision.ESCALATE,
                    "Account access, security lockouts, and identity verification require secure authentication via iforgot.apple.com or human security advisor."
            );
        }
        if ("BILLING_SUBSCRIPTIONS".equalsIgnoreCase(intent)) {
            return new EscalationDecision(
                    Decision.ESCALATE,
                    "Financial billing inquiries, unauthorized credit card charges, and subscription refunds require private transaction records and account-specific review."
            );
        }

        // 4. LLM Escalation Triage (if ChatModel configured and available)
        if (chatModel != null) {
            try {
                String promptText = buildPrompt(customerMessage, intent, confidence, similarConversations);
                String responseText = chatModel.call(promptText);
                EscalationDecision llmDecision = parseLlmResponse(responseText);
                if (llmDecision != null) {
                    return llmDecision;
                }
            } catch (Exception e) {
                log.warn("LLM escalation decision failed ({}), using policy default", e.getMessage());
            }
        }

        // 5. Default Policy for Standard Troubleshooting Inquiries
        return new EscalationDecision(
                Decision.AUTO_HANDLE,
                "Standard automated support inquiry resolvable via troubleshooting documentation."
        );
    }

    private String buildPrompt(String customerMessage, String intent, double confidence,
                               List<SimilarConversation> similarConversations) {
        try {
            String template;
            try (InputStream is = promptResource.getInputStream()) {
                template = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            }
            StringBuilder convsBuilder = new StringBuilder();
            if (similarConversations != null) {
                for (SimilarConversation sc : similarConversations) {
                    convsBuilder.append(String.format("- Customer: \"%s\" -> Agent: \"%s\"%n", sc.customerText(), sc.agentReply()));
                }
            }
            return template
                    .replace("{brand}", brand)
                    .replace("{intent}", intent != null ? intent : "GENERAL_PRODUCT_INQUIRY")
                    .replace("{confidence}", String.format("%.2f", confidence))
                    .replace("{confidence_threshold}", String.format("%.2f", confidenceThreshold))
                    .replace("{similar_conversations}", convsBuilder.toString())
                    .replace("{customer_message}", customerMessage);
        } catch (Exception e) {
            return "Decide escalation for message: " + customerMessage;
        }
    }

    private EscalationDecision parseLlmResponse(String rawResponse) {
        if (rawResponse == null || rawResponse.isBlank()) return null;
        try {
            String jsonStr = rawResponse.trim();
            if (jsonStr.contains("{") && jsonStr.contains("}")) {
                jsonStr = jsonStr.substring(jsonStr.indexOf("{"), jsonStr.lastIndexOf("}") + 1);
            }
            JsonNode node = objectMapper.readTree(jsonStr);
            String decStr = node.path("decision").asText("AUTO_HANDLE").trim().toUpperCase();
            String reason = node.path("reason").asText("Automated assessment");
            Decision dec = "ESCALATE".equals(decStr) ? Decision.ESCALATE : Decision.AUTO_HANDLE;
            return new EscalationDecision(dec, reason);
        } catch (Exception e) {
            log.debug("Could not parse LLM escalation JSON: '{}'", rawResponse);
        }
        return null;
    }
}
