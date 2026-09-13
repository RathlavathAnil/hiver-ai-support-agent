package com.hiver.supportagent.repository;

import com.hiver.supportagent.model.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ConversationRepository extends JpaRepository<Conversation, Long> {

    List<Conversation> findByBrand(String brand);

    List<Conversation> findByBrandAndIntent(String brand, String intent);

    @Query("SELECT DISTINCT c.intent FROM Conversation c WHERE c.brand = :brand AND c.intent IS NOT NULL")
    List<String> findDistinctIntentsByBrand(@Param("brand") String brand);

    long countByBrand(String brand);
}
