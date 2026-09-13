package com.hiver.supportagent.service;

import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.regex.Pattern;

/**
 * Validates generated draft replies for guardrail compliance before delivering to API response.
 */
@Component
public class ResponseValidator {

    private static final Logger log = LoggerFactory.getLogger(ResponseValidator.class);

    private static final Pattern PROMPT_LEAK_PATTERN = Pattern.compile(
            "(\\{\\{|##\\s*Guidelines|##\\s*Response|##\\s*Context|##\\s*Similar|System\\s*Prompt|Your Reply:)",
            Pattern.CASE_INSENSITIVE
    );

    private static final Pattern FINANCIAL_PROMISE_PATTERN = Pattern.compile(
            "(i have (refunded|credited|reversed your charge)|i (processed|sent) your refund|your money has been returned)",
            Pattern.CASE_INSENSITIVE
    );

    public String validateAndSanitize(String rawReply, String customerMessage, EscalationDecision escalation) {
        if (rawReply == null || rawReply.isBlank()) {
            log.warn("Generated reply was empty/null. Providing fallback response.");
            return getSafeFallback(escalation);
        }

        String reply = rawReply.trim();

        // 1. Guardrail: Prompt leak check
        if (PROMPT_LEAK_PATTERN.matcher(reply).find()) {
            log.warn("Prompt leak pattern detected in reply: '{}'. Falling back.", reply);
            return getSafeFallback(escalation);
        }

        // 2. Guardrail: Unauthorized financial promises check
        if (FINANCIAL_PROMISE_PATTERN.matcher(reply).find()) {
            log.warn("Unauthorized financial promise detected in reply: '{}'. Replacing with policy reply.", reply);
            return "We understand you have a billing inquiry. For refund requests and account verification, please sign in to reportaproblem.apple.com to manage your purchases.";
        }

        // 3. Length sanity check
        if (reply.length() > 600) {
            log.debug("Reply length exceeds 600 characters ({}); truncating cleanly.", reply.length());
            reply = reply.substring(0, 500) + "...";
        }

        return reply;
    }

    private String getSafeFallback(EscalationDecision escalation) {
        if (escalation != null && escalation.decision() == Decision.ESCALATE) {
            return "We'd be glad to look into this for you. As this issue requires human advisor assistance, please connect directly with our support team: https://support.apple.com/contact";
        }
        return "We're here to help! To get started, could you let us know your exact device model and iOS version? Have you tried restarting your device?";
    }
}
