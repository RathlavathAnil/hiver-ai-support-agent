package com.hiver.supportagent.util;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PiiSanitizerTest {

    private PiiSanitizer sanitizer;

    @BeforeEach
    void setUp() {
        sanitizer = new PiiSanitizer();
    }

    @Test
    @DisplayName("Should scrub email addresses")
    void testScrubEmails() {
        String input = "Please contact me at john.doe@example.com for my account issues.";
        String result = sanitizer.sanitize(input);
        assertFalse(result.contains("john.doe@example.com"));
        assertTrue(result.contains("[EMAIL]"));
    }

    @Test
    @DisplayName("Should scrub phone numbers")
    void testScrubPhoneNumbers() {
        String input = "Call me at +1-800-555-0199 or (555) 123-4567 regarding my repair.";
        String result = sanitizer.sanitize(input);
        assertFalse(result.contains("555-0199"));
        assertTrue(result.contains("[PHONE]"));
    }

    @Test
    @DisplayName("Should scrub Twitter @mentions")
    void testScrubMentions() {
        String input = "@AppleSupport my phone is broken, help @115858!";
        String result = sanitizer.sanitize(input);
        assertFalse(result.contains("@AppleSupport"));
        assertTrue(result.contains("[USER]"));
    }

    @Test
    @DisplayName("Should handle empty or blank inputs")
    void testEmptyInputs() {
        assertEquals("", sanitizer.sanitize(""));
        assertEquals("", sanitizer.sanitize(null));
        assertEquals("", sanitizer.sanitize("   "));
    }
}
