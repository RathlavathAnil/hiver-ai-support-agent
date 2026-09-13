package com.hiver.supportagent.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hiver.supportagent.model.AgentResponse;
import com.hiver.supportagent.model.CustomerMessage;
import com.hiver.supportagent.model.EscalationDecision;
import com.hiver.supportagent.model.EscalationDecision.Decision;
import com.hiver.supportagent.service.SupportAgentOrchestrator;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SupportController.class)
class SupportControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private SupportAgentOrchestrator orchestrator;

    @Test
    @DisplayName("GET /api/v1/support/health should return 200 OK")
    void testHealthEndpoint() throws Exception {
        mockMvc.perform(get("/api/v1/support/health"))
                .andExpect(status().isOk())
                .andExpect(content().string("AI Support Agent is running"));
    }

    @Test
    @DisplayName("POST /api/v1/support with valid payload should return 200 OK with AgentResponse")
    void testValidSupportRequest() throws Exception {
        AgentResponse mockResponse = new AgentResponse(
                "BATTERY_PERFORMANCE",
                0.95,
                "Check Settings > Battery",
                new EscalationDecision(Decision.AUTO_HANDLE, "Normal troubleshooting"),
                Collections.emptyList()
        );

        when(orchestrator.processMessage(anyString())).thenReturn(mockResponse);

        CustomerMessage request = new CustomerMessage("My battery dies very fast.");

        mockMvc.perform(post("/api/v1/support")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.intent").value("BATTERY_PERFORMANCE"))
                .andExpect(jsonPath("$.confidence").value(0.95))
                .andExpect(jsonPath("$.escalation.decision").value("AUTO_HANDLE"))
                .andExpect(jsonPath("$.reply").value("Check Settings > Battery"));
    }

    @Test
    @DisplayName("POST /api/v1/support with blank message should return 400 Bad Request")
    void testBlankSupportRequest() throws Exception {
        CustomerMessage blankRequest = new CustomerMessage("   ");

        mockMvc.perform(post("/api/v1/support")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(blankRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.fieldErrors.message").exists());
    }
}
