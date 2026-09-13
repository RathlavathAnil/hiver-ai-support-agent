package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class EscalationServiceTest {

    private EscalationServiceImpl escalationService;

    @BeforeEach
    void setUp() {
        escalationService = new EscalationServiceImpl(new ObjectMapper());
        ReflectionTestUtils.setField(escalationService, "confidenceThreshold", 0.60);
        ReflectionTestUtils.setField(escalationService, "escalationKeywords", List.of(
                "cancel", "legal", "lawyer", "manager", "refund", "sue", "fraud", "hacked", "stolen", "crack", "water damage"
        ));
    }

    @Test
    @DisplayName("Should auto-handle standard software update inquiry")
    void testAutoHandleSoftwareUpdate() {
        String msg = "How do I update to iOS 11?";
        var decision = escalationService.decide(msg, "SOFTWARE_UPDATE_OS", 0.92, Collections.emptyList());
        assertEquals(Decision.AUTO_HANDLE, decision.decision());
        assertNotNull(decision.reason());
    }

    @Test
    @DisplayName("Should escalate on high-risk keyword 'lawyer'")
    void testEscalateOnKeyword() {
        String msg = "Your update broke my phone and I will speak to my lawyer if not fixed.";
        var decision = escalationService.decide(msg, "SOFTWARE_UPDATE_OS", 0.90, Collections.emptyList());
        assertEquals(Decision.ESCALATE, decision.decision());
        assertTrue(decision.reason().contains("lawyer"));
    }

    @Test
    @DisplayName("Should escalate on low confidence classification")
    void testEscalateOnLowConfidence() {
        String msg = "Something strange happens when I tap things.";
        var decision = escalationService.decide(msg, "GENERAL_PRODUCT_INQUIRY", 0.45, Collections.emptyList());
        assertEquals(Decision.ESCALATE, decision.decision());
        assertTrue(decision.reason().contains("confidence"));
    }

    @Test
    @DisplayName("Should escalate physical hardware damage intent by policy")
    void testEscalateHardwareDamage() {
        String msg = "My screen is cracked and I need it fixed.";
        var decision = escalationService.decide(msg, "HARDWARE_PHYSICAL_DAMAGE", 0.95, Collections.emptyList());
        assertEquals(Decision.ESCALATE, decision.decision());
        assertTrue(decision.reason().contains("hardware") || decision.reason().contains("Genius Bar"));
    }

    @Test
    @DisplayName("Should escalate billing subscription intent by policy")
    void testEscalateBilling() {
        String msg = "I have an unauthorized charge on my account.";
        var decision = escalationService.decide(msg, "BILLING_SUBSCRIPTIONS", 0.95, Collections.emptyList());
        assertEquals(Decision.ESCALATE, decision.decision());
        assertTrue(decision.reason().contains("Financial") || decision.reason().contains("billing"));
    }
}
