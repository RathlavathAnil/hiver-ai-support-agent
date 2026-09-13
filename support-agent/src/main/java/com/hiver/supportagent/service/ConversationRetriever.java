package com.hiver.supportagent.service;

import com.hiver.supportagent.model.AgentResponse.SimilarConversation;
import java.util.List;

/**
 * Retrieves similar historical conversations using vector similarity search (pgvector).
 */
public interface ConversationRetriever {

    /**
     * Find the most similar historical conversations to the given message.
     *
     * @param customerMessage the message to find similar conversations for
     * @param topK maximum number of results
     * @return list of similar conversations ordered by similarity (descending)
     */
    List<SimilarConversation> findSimilar(String customerMessage, int topK);
}
