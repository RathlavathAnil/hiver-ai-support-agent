package com.hiver.supportagent.service;

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

/**
 * Real reply generation service.
 * Hybrid: Uses Spring AI LLM with RAG grounding when available, with a deterministic brand synthesis fallback.
 */
@Service
public class ReplyGeneratorImpl implements ReplyGenerator {

    private static final Logger log = LoggerFactory.getLogger(ReplyGeneratorImpl.class);

    @Value("classpath:prompts/reply_generation.st")
    private Resource promptResource;

    @Value("${app.brand:AppleSupport}")
    private String brand;

    @Autowired(required = false)
    private org.springframework.ai.chat.model.ChatModel chatModel;

    @Override
    public String generateReply(String customerMessage, String intent, List<SimilarConversation> similarConversations) {
        // 1. Try LLM generation with RAG context
        if (chatModel != null) {
            try {
                String promptText = buildPrompt(customerMessage, intent, similarConversations);
                String responseText = chatModel.call(promptText);
                if (responseText != null && !responseText.isBlank()) {
                    String clean = cleanGeneratedReply(responseText);
                    log.debug("Generated LLM reply: {}", clean);
                    return clean;
                }
            } catch (Exception e) {
                log.warn("LLM reply generation failed ({}), falling back to grounded template synthesis", e.getMessage());
            }
        }

        // 2. Deterministic grounded response synthesis
        return synthesizeGroundedReply(customerMessage, intent, similarConversations);
    }

    private String synthesizeGroundedReply(String customerMessage, String intent, List<SimilarConversation> similarConversations) {
        // If we have high similarity historical resolution, adapt its structure
        if (similarConversations != null && !similarConversations.isEmpty()) {
            SimilarConversation top = similarConversations.get(0);
            if (top.similarityScore() >= 0.50 && top.agentReply() != null && !top.agentReply().isBlank()) {
                String historical = top.agentReply().trim();
                // If historical reply has actionable troubleshooting guidance or official support links, use clean synthesis
                if (historical.contains("Settings") || historical.contains("restart") || historical.contains("support.apple.com") || historical.contains("http")) {
                    log.debug("[REPLY_GENERATOR] Grounding reply directly in historical support pattern (similarity: {:.4f})", top.similarityScore());
                    return historical;
                }
            }
        }

        // Intent-grounded resolution templates
        return switch (intent != null ? intent : "GENERAL_PRODUCT_INQUIRY") {
            case "SOFTWARE_UPDATE_OS" ->
                    "We'd like to help with your update issue. Have you tried restarting your device? What exact iOS version and device model are you using? https://support.apple.com/ios/update";
            case "BATTERY_PERFORMANCE" ->
                    "We're here to help with your battery life. Could you check Settings > Battery > Battery Health to see your Maximum Capacity percentage? What device are you using?";
            case "HARDWARE_PHYSICAL_DAMAGE" ->
                    "We understand this is frustrating. For screen repairs and physical damage inspections, please schedule a Genius Bar appointment or check repair options: https://support.apple.com/repair";
            case "ACCOUNT_ACCESS_SECURITY" ->
                    "Your account security is our priority. For password resets and Apple ID recovery, please visit iforgot.apple.com or contact Apple Support directly: https://support.apple.com/apple-id";
            case "APP_CRASH_PERFORMANCE" ->
                    "Let's get this working smoothly. Try force closing the app, checking the App Store for updates, and restarting your device. More help: https://support.apple.com/HT201398";
            case "NETWORK_CONNECTIVITY" ->
                    "We're happy to help you stay connected. Try toggling Airplane Mode on/off, or reset network settings under Settings > General > Reset > Reset Network Settings.";
            case "BILLING_SUBSCRIPTIONS" ->
                    "We can help guide you on billing. You can view, manage, and request refunds for subscriptions at reportaproblem.apple.com or under Settings > [Your Name] > Subscriptions.";
            case "AUDIO_SOUND_ISSUES" ->
                    "Let's look into your audio issue. Please check Settings > Sounds & Haptics, test with Voice Memos, and ensure the speakers/receivers are clear of any debris.";
            case "ICLOUD_STORAGE_SYNC" ->
                    "We'd love to help with iCloud. You can manage your storage and backups under Settings > [Your Name] > iCloud > Manage Storage: https://support.apple.com/HT204247";
            default ->
                    "We're here to help! Could you share a few more details about the issue you're experiencing, along with your device model and OS version?";
        };
    }

    private String buildPrompt(String customerMessage, String intent, List<SimilarConversation> similarConversations) {
        try {
            String template;
            try (InputStream is = promptResource.getInputStream()) {
                template = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            }
            StringBuilder convsBuilder = new StringBuilder();
            if (similarConversations != null) {
                for (int i = 0; i < Math.min(3, similarConversations.size()); i++) {
                    SimilarConversation sc = similarConversations.get(i);
                    convsBuilder.append(String.format("Example %d:%nCustomer: \"%s\"%nApple Reply: \"%s\"%n%n",
                            i + 1, sc.customerText(), sc.agentReply()));
                }
            }
            return template
                    .replace("{brand}", brand)
                    .replace("{intent}", intent != null ? intent : "GENERAL_PRODUCT_INQUIRY")
                    .replace("{similar_conversations}", convsBuilder.toString())
                    .replace("{customer_message}", customerMessage);
        } catch (Exception e) {
            return "Draft a support reply for: " + customerMessage;
        }
    }

    private String cleanGeneratedReply(String text) {
        String cleaned = text.trim();
        if (cleaned.startsWith("\"") && cleaned.endsWith("\"") && cleaned.length() > 2) {
            cleaned = cleaned.substring(1, cleaned.length() - 1).trim();
        }
        if (cleaned.startsWith("Your Reply:") || cleaned.startsWith("Reply:")) {
            cleaned = cleaned.substring(cleaned.indexOf(":") + 1).trim();
        }
        return cleaned;
    }
}
