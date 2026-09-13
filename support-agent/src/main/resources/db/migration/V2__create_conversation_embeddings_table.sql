-- V2__create_conversation_embeddings_table.sql
-- Vector embeddings table for semantic similarity search via pgvector

CREATE TABLE IF NOT EXISTS conversation_embeddings (
    id                BIGSERIAL PRIMARY KEY,
    conversation_id   BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    embedding         vector(768),  -- Gemini embedding dimension
    model_name        VARCHAR(128) DEFAULT 'gemini-embedding-001',
    created_at        TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE
);

-- HNSW index for fast approximate nearest-neighbor search
-- Using cosine distance (<=>) which is standard for text embeddings
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON conversation_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_embeddings_conversation_id
    ON conversation_embeddings(conversation_id);
