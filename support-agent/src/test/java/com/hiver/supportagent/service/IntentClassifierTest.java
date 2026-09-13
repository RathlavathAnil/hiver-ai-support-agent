package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;

class IntentClassifierTest {

    private IntentClassifierImpl classifier;

    @BeforeEach
    void setUp() {
        classifier = new IntentClassifierImpl(new ObjectMapper());
    }

    @Test
    @DisplayName("Should classify battery issues correctly")
    void testBatteryClassification() {
        String msg = "My iPhone battery is draining so fast after updating, it dies in 2 hours.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("BATTERY_PERFORMANCE", result.intent());
        assertTrue(result.confidence() >= 0.85);
    }

    @Test
    @DisplayName("Should classify OS update issues correctly")
    void testSoftwareUpdateClassification() {
        String msg = "Getting an error trying to install the new iOS 11 update on my phone.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("SOFTWARE_UPDATE_OS", result.intent());
        assertTrue(result.confidence() >= 0.85);
    }

    @Test
    @DisplayName("Should classify hardware damage correctly")
    void testHardwareDamageClassification() {
        String msg = "I dropped my iPhone and the screen is completely cracked and shattered.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("HARDWARE_PHYSICAL_DAMAGE", result.intent());
        assertTrue(result.confidence() >= 0.90);
    }

    @Test
    @DisplayName("Should classify account security lockout correctly")
    void testAccountSecurityClassification() {
        String msg = "I forgot my Apple ID password and my account is locked out, verification code not coming.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("ACCOUNT_ACCESS_SECURITY", result.intent());
        assertTrue(result.confidence() >= 0.90);
    }

    @Test
    @DisplayName("Should classify billing and refunds correctly")
    void testBillingClassification() {
        String msg = "I was charged twice for my Apple Music subscription and need a refund.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("BILLING_SUBSCRIPTIONS", result.intent());
        assertTrue(result.confidence() >= 0.90);
    }

    @Test
    @DisplayName("Should classify app crash correctly")
    void testAppCrashClassification() {
        String msg = "Every time I open the camera app it freezes and crashes immediately.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("APP_CRASH_PERFORMANCE", result.intent());
        assertTrue(result.confidence() >= 0.85);
    }

    @Test
    @DisplayName("Should classify wifi and network issues correctly")
    void testNetworkClassification() {
        String msg = "My phone keeps disconnecting from Wi-Fi and bluetooth won't pair with my headphones.";
        var result = classifier.classify(msg, Collections.emptyList());
        assertEquals("NETWORK_CONNECTIVITY", result.intent());
        assertTrue(result.confidence() >= 0.85);
    }
}
