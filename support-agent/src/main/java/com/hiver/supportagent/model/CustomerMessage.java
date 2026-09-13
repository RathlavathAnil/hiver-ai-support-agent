package com.hiver.supportagent.model;

import jakarta.validation.constraints.NotBlank;

/**
 * Incoming customer message request payload.
 */
public record CustomerMessage(
        @NotBlank(message = "Message cannot be blank")
        String message
) {}
