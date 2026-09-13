package com.hiver.supportagent.util;

import org.springframework.stereotype.Component;
import java.util.regex.Pattern;

/**
 * Utility to scrub sensitive PII (emails, phone numbers, payment cards, @mentions)
 * from incoming customer messages before processing, logging, or LLM transmission.
 */
@Component
public class PiiSanitizer {

    private static final Pattern EMAIL_PATTERN = Pattern.compile(
            "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", Pattern.CASE_INSENSITIVE);

    private static final Pattern PHONE_PATTERN = Pattern.compile(
            "\\b(?:\\+?\\d{1,3}[-.\\s]?)?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b");

    private static final Pattern CARD_PATTERN = Pattern.compile(
            "\\b(?:\\d{4}[-\\s]?){3}\\d{4}\\b");

    private static final Pattern MENTION_PATTERN = Pattern.compile(
            "@\\w+");

    public String sanitize(String input) {
        if (input == null || input.isBlank()) {
            return "";
        }
        String sanitized = EMAIL_PATTERN.matcher(input).replaceAll("[EMAIL]");
        sanitized = PHONE_PATTERN.matcher(sanitized).replaceAll("[PHONE]");
        sanitized = CARD_PATTERN.matcher(sanitized).replaceAll("[CARD_REDACTED]");
        sanitized = MENTION_PATTERN.matcher(sanitized).replaceAll("[USER]");
        return sanitized.trim().replaceAll("\\s+", " ");
    }
}
