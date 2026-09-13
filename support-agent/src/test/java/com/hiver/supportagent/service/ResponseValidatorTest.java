package com.hiver.supportagent.service;

import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ResponseValidatorTest {

    private ResponseValidator validator;

    @BeforeEach
    void setUp() {
        validator = new ResponseValidator();
    }

    @Test
    @DisplayName("Should pass valid grounded reply")
    void testValidReply() {
        String reply = "We'd like to help. Have you tried restarting your device?";
        var escalation = new EscalationDecision(Decision.AUTO_HANDLE, "Normal");
        String result = validator.validateAndSanitize(reply, "My phone froze", escalation);
        assertEquals(reply, result);
    }

    @Test
    @DisplayName("Should sanitize prompt leakage tokens")
    void testPromptLeakageSanitization() {
        String leakedReply = "## Guidelines 1. Be helpful. {{Your Reply: Hello}}";
        var escalation = new EscalationDecision(Decision.AUTO_HANDLE, "Normal");
        String result = validator.validateAndSanitize(leakedReply, "My phone froze", escalation);
        assertFalse(result.contains("## Guidelines"));
        assertFalse(result.contains("{{"));
        assertTrue(result.contains("We're here to help"));
    }

    @Test
    @DisplayName("Should block unauthorized financial promise")
    void testFinancialPromiseBlock() {
        String unsafeReply = "I have refunded $50 to your credit card immediately.";
        var escalation = new EscalationDecision(Decision.ESCALATE, "Billing issue");
        String result = validator.validateAndSanitize(unsafeReply, "Refund please", escalation);
        assertFalse(result.contains("I have refunded"));
        assertTrue(result.contains("reportaproblem.apple.com"));
    }

    @Test
    @DisplayName("Should provide escalation fallback for empty reply when escalated")
    void testEmptyReplyEscalationFallback() {
        var escalation = new EscalationDecision(Decision.ESCALATE, "Screen crack");
        String result = validator.validateAndSanitize("", "Broken screen", escalation);
        assertTrue(result.contains("support.apple.com/contact"));
    }
}
