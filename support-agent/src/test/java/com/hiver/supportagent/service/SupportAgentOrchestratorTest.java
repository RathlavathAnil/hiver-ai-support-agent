package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse;
import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import com.hiver.supportagent.service.IntentClassifier.IntentResult;
import com.hiver.supportagent.util.PiiSanitizer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

class SupportAgentOrchestratorTest {

    private ConversationRetriever conversationRetriever;
    private IntentClassifier intentClassifier;
    private ReplyGenerator replyGenerator;
    private EscalationService escalationService;
    private ResponseValidator responseValidator;
    private PiiSanitizer piiSanitizer;
    private SupportAgentOrchestrator orchestrator;

    @BeforeEach
    void setUp() {
        conversationRetriever = Mockito.mock(ConversationRetriever.class);
        intentClassifier = Mockito.mock(IntentClassifier.class);
        replyGenerator = Mockito.mock(ReplyGenerator.class);
        escalationService = Mockito.mock(EscalationService.class);
        responseValidator = Mockito.mock(ResponseValidator.class);
        piiSanitizer = new PiiSanitizer();

        orchestrator = new SupportAgentOrchestratorImpl(
                piiSanitizer,
                conversationRetriever,
                intentClassifier,
                replyGenerator,
                escalationService,
                responseValidator
        );
    }

    @Test
    @DisplayName("Should orchestrate full pipeline successfully")
    void testFullPipeline() {
        String rawMsg = "My battery drains on iOS 11, email me at test@example.com";
        List<SimilarConversation> mockConvs = List.of(
                new SimilarConversation("Battery issue", "Check battery health", "BATTERY_PERFORMANCE", 0.88)
        );

        when(conversationRetriever.findSimilar(anyString(), anyInt())).thenReturn(mockConvs);
        when(intentClassifier.classify(anyString(), anyList()))
                .thenReturn(new IntentResult("BATTERY_PERFORMANCE", 0.92));
        when(replyGenerator.generateReply(anyString(), eq("BATTERY_PERFORMANCE"), anyList()))
                .thenReturn("We'd be glad to help with your battery.");
        when(escalationService.decide(anyString(), eq("BATTERY_PERFORMANCE"), eq(0.92), anyList()))
                .thenReturn(new EscalationDecision(Decision.AUTO_HANDLE, "Standard troubleshooting"));
        when(responseValidator.validateAndSanitize(anyString(), anyString(), any()))
                .thenReturn("We'd be glad to help with your battery.");

        AgentResponse response = orchestrator.processMessage(rawMsg);

        assertNotNull(response);
        assertEquals("BATTERY_PERFORMANCE", response.intent());
        assertEquals(0.92, response.confidence(), 0.001);
        assertEquals(Decision.AUTO_HANDLE, response.escalation().decision());
        assertEquals("We'd be glad to help with your battery.", response.reply());
        assertEquals(1, response.similarConversations().size());
    }
}
