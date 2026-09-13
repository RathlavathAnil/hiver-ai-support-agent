package com.hiver.supportagent.model;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * Represents a customer-agent conversation pair extracted from the Twitter dataset.
 * Each record contains one customer message and the corresponding brand agent reply.
 */
@Entity
@Table(name = "conversations")
public class Conversation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tweet_id", nullable = false, unique = true)
    private String tweetId;

    @Column(name = "thread_id")
    private String threadId;

    @Column(nullable = false)
    private String brand;

    @Column(name = "customer_text", nullable = false, columnDefinition = "TEXT")
    private String customerText;

    @Column(name = "agent_reply", columnDefinition = "TEXT")
    private String agentReply;

    @Column
    private String intent;

    @Column(name = "created_at")
    private Instant createdAt;

    // Constructors
    public Conversation() {}

    public Conversation(String tweetId, String brand, String customerText, String agentReply) {
        this.tweetId = tweetId;
        this.brand = brand;
        this.customerText = customerText;
        this.agentReply = agentReply;
    }

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTweetId() { return tweetId; }
    public void setTweetId(String tweetId) { this.tweetId = tweetId; }

    public String getThreadId() { return threadId; }
    public void setThreadId(String threadId) { this.threadId = threadId; }

    public String getBrand() { return brand; }
    public void setBrand(String brand) { this.brand = brand; }

    public String getCustomerText() { return customerText; }
    public void setCustomerText(String customerText) { this.customerText = customerText; }

    public String getAgentReply() { return agentReply; }
    public void setAgentReply(String agentReply) { this.agentReply = agentReply; }

    public String getIntent() { return intent; }
    public void setIntent(String intent) { this.intent = intent; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
