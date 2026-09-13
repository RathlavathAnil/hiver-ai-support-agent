package com.hiver.supportagent.controller;

import com.hiver.supportagent.model.AgentResponse;
import com.hiver.supportagent.model.CustomerMessage;
import com.hiver.supportagent.service.SupportAgentOrchestrator;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller for the AI customer support agent.
 * Single endpoint that classifies intent, generates reply, and decides escalation.
 */
@RestController
@RequestMapping("/api/v1/support")
public class SupportController {

    private static final Logger log = LoggerFactory.getLogger(SupportController.class);

    private final SupportAgentOrchestrator orchestrator;

    public SupportController(SupportAgentOrchestrator orchestrator) {
        this.orchestrator = orchestrator;
    }

    /**
     * Process an incoming customer support message.
     *
     * @param request the customer's message
     * @return complete agent response with intent, reply, and escalation decision
     */
    @PostMapping
    public ResponseEntity<AgentResponse> handleSupportRequest(
            @Valid @RequestBody CustomerMessage request) {
        log.info("Received support request: {}", truncate(request.message(), 100));

        AgentResponse response = orchestrator.processMessage(request.message());

        log.info("Response — intent={}, decision={}, confidence={}",
                response.intent(), response.escalation().decision(), response.confidence());

        return ResponseEntity.ok(response);
    }

    /**
     * Health/info endpoint for quick verification.
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("AI Support Agent is running");
    }

    private String truncate(String text, int maxLen) {
        return text.length() <= maxLen ? text : text.substring(0, maxLen) + "...";
    }
}
