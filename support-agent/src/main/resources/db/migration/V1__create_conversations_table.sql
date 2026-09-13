-- V1__create_conversations_table.sql
-- Core table for storing processed customer-agent conversation pairs

CREATE TABLE IF NOT EXISTS conversations (
    id              BIGSERIAL PRIMARY KEY,
    tweet_id        VARCHAR(64) NOT NULL UNIQUE,
    thread_id       VARCHAR(64),
    brand           VARCHAR(64) NOT NULL,
    customer_text   TEXT NOT NULL,
    agent_reply     TEXT,
    intent          VARCHAR(64),
    created_at      TIMESTAMPTZ,

    -- Indexes for common queries
    CONSTRAINT conversations_tweet_id_unique UNIQUE (tweet_id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_brand ON conversations(brand);
CREATE INDEX IF NOT EXISTS idx_conversations_brand_intent ON conversations(brand, intent);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_id ON conversations(thread_id);
