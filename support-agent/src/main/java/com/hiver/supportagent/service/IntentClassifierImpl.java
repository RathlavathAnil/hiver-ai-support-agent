package com.hiver.supportagent.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
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
 * Real intent classification service.
 * Hybrid: Uses Spring AI LLM when available, with a deterministic rule/regex fallback.
 */
@Service
public class IntentClassifierImpl implements IntentClassifier {

    private static final Logger log = LoggerFactory.getLogger(IntentClassifierImpl.class);

    private static final List<String> TAXONOMY = List.of(
            "SOFTWARE_UPDATE_OS",
            "BATTERY_PERFORMANCE",
            "HARDWARE_PHYSICAL_DAMAGE",
            "ACCOUNT_ACCESS_SECURITY",
            "APP_CRASH_PERFORMANCE",
            "NETWORK_CONNECTIVITY",
            "BILLING_SUBSCRIPTIONS",
            "AUDIO_SOUND_ISSUES",
            "ICLOUD_STORAGE_SYNC",
            "GENERAL_PRODUCT_INQUIRY"
    );

    // Intent Heuristic Regex Patterns
    private static final Pattern PATTERN_SOFTWARE_UPDATE = Pattern.compile(
            "\\b(ios\\s*\\d+|update|updating|updated|install|downgrade|boot loop|apple logo|beta|sierra|macos)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_BATTERY = Pattern.compile(
            "\\b(battery|batteries|draining|drain|charge|charging|overheat|overheating|dying fast|power off)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_HARDWARE = Pattern.compile(
            "\\b(crack|cracked|broken|shattered|shatter|damaged|water damage|dropped in|screen replacement|genius bar|repair cost|cost to fix)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_ACCOUNT_SECURITY = Pattern.compile(
            "\\b(apple id|icloud lock|activation lock|password|passcode|locked out|verification code|two factor|2fa|hacked|stolen phone)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_APP_CRASH = Pattern.compile(
            "\\b(crash|crashes|crashing|freeze|freezes|freezing|lag|laggy|lagging|slow|unresponsive|black screen|frozen screen|touch not working)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_NETWORK = Pattern.compile(
            "\\b(wi-?fi|bluetooth|cellular|no service|signal|hotspot|airdrop|lte|pairing|disconnecting)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_BILLING = Pattern.compile(
            "\\b(billing|charge|charged|refund|subscription|subscriptions|apple music|itunes store|receipt|unauthorized purchase|payment declined)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_AUDIO = Pattern.compile(
            "\\b(sound|audio|speaker|mic|microphone|earpiece|volume|muffled|static|can't hear|headphone mode)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern PATTERN_ICLOUD = Pattern.compile(
            "\\b(icloud storage|storage full|backup|sync|photos not syncing|restore backup|manage storage)\\b", Pattern.CASE_INSENSITIVE);

    @Value("classpath:prompts/intent_classification.st")
    private Resource promptResource;

    @Value("${app.brand:AppleSupport}")
    private String brand;

    private final ObjectMapper objectMapper;

    // Optional Spring AI ChatClient/ChatModel (if configured via Vertex AI Gemini)
    @Autowired(required = false)
    private org.springframework.ai.chat.model.ChatModel chatModel;

    public IntentClassifierImpl(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public IntentResult classify(String customerMessage, List<SimilarConversation> similarConversations) {
        if (customerMessage == null || customerMessage.isBlank()) {
            return new IntentResult("GENERAL_PRODUCT_INQUIRY", 0.30);
        }

        // 1. Try LLM classification if ChatModel is available
        if (chatModel != null) {
            try {
                String promptText = buildPrompt(customerMessage, similarConversations);
                String responseText = chatModel.call(promptText);
                IntentResult result = parseLlmResponse(responseText);
                if (result != null && TAXONOMY.contains(result.intent())) {
                    log.debug("LLM Classified intent: {} with confidence {}", result.intent(), result.confidence());
                    return result;
                }
            } catch (Exception e) {
                log.warn("LLM Intent Classification failed ({}), falling back to deterministic classifier", e.getMessage());
            }
        }

        // 2. Deterministic / Heuristic Rule-based Classification
        return classifyRuleBased(customerMessage, similarConversations);
    }

    public IntentResult classifyRuleBased(String text, List<SimilarConversation> similarConversations) {
        String lower = text.toLowerCase();

        // Check patterns in order of specificity
        if (PATTERN_ACCOUNT_SECURITY.matcher(lower).find()) {
            return new IntentResult("ACCOUNT_ACCESS_SECURITY", 0.94);
        }
        if (PATTERN_BILLING.matcher(lower).find()) {
            return new IntentResult("BILLING_SUBSCRIPTIONS", 0.92);
        }
        if (PATTERN_HARDWARE.matcher(lower).find()) {
            return new IntentResult("HARDWARE_PHYSICAL_DAMAGE", 0.95);
        }
        if (PATTERN_BATTERY.matcher(lower).find()) {
            return new IntentResult("BATTERY_PERFORMANCE", 0.90);
        }
        if (PATTERN_AUDIO.matcher(lower).find()) {
            return new IntentResult("AUDIO_SOUND_ISSUES", 0.88);
        }
        if (PATTERN_ICLOUD.matcher(lower).find()) {
            return new IntentResult("ICLOUD_STORAGE_SYNC", 0.88);
        }
        if (PATTERN_NETWORK.matcher(lower).find()) {
            return new IntentResult("NETWORK_CONNECTIVITY", 0.89);
        }
        if (PATTERN_SOFTWARE_UPDATE.matcher(lower).find()) {
            return new IntentResult("SOFTWARE_UPDATE_OS", 0.91);
        }
        if (PATTERN_APP_CRASH.matcher(lower).find()) {
            return new IntentResult("APP_CRASH_PERFORMANCE", 0.87);
        }

        // Check if top retrieved conversation has high similarity
        if (similarConversations != null && !similarConversations.isEmpty()) {
            SimilarConversation top = similarConversations.get(0);
            if (top.similarityScore() > 0.65 && top.intent() != null && TAXONOMY.contains(top.intent())) {
                return new IntentResult(top.intent(), Math.min(0.80, top.similarityScore()));
            }
        }

        return new IntentResult("GENERAL_PRODUCT_INQUIRY", 0.50);
    }

    private String buildPrompt(String customerMessage, List<SimilarConversation> similarConversations) {
        try {
            String template;
            try (InputStream is = promptResource.getInputStream()) {
                template = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            }
            StringBuilder convsBuilder = new StringBuilder();
            if (similarConversations != null) {
                for (int i = 0; i < Math.min(3, similarConversations.size()); i++) {
                    SimilarConversation sc = similarConversations.get(i);
                    convsBuilder.append(String.format("- Customer: \"%s\" -> Intent: %s%n", sc.customerText(), sc.intent()));
                }
            }
            return template
                    .replace("{brand}", brand)
                    .replace("{intent_list}", String.join("\n", TAXONOMY.stream().map(s -> "- " + s).toList()))
                    .replace("{similar_conversations}", convsBuilder.toString())
                    .replace("{customer_message}", customerMessage);
        } catch (Exception e) {
            return "Classify the intent for customer message: " + customerMessage;
        }
    }

    private IntentResult parseLlmResponse(String rawResponse) {
        if (rawResponse == null || rawResponse.isBlank()) return null;
        try {
            String jsonStr = rawResponse.trim();
            if (jsonStr.contains("{") && jsonStr.contains("}")) {
                jsonStr = jsonStr.substring(jsonStr.indexOf("{"), jsonStr.lastIndexOf("}") + 1);
            }
            JsonNode node = objectMapper.readTree(jsonStr);
            String intent = node.path("intent").asText(null);
            double confidence = node.path("confidence").asDouble(0.85);
            if (intent != null && !intent.isBlank()) {
                return new IntentResult(intent.trim(), confidence);
            }
        } catch (Exception e) {
            log.debug("Could not parse LLM JSON intent response: '{}'", rawResponse);
        }
        return null;
    }
}
