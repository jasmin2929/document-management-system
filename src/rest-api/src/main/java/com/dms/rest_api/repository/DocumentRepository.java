package com.dms.rest_api.repository;

import com.dms.rest_api.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Spring Data JPA Repository for Document entities.
 */
@Repository
public interface DocumentRepository extends JpaRepository<Document, Long> {

    /**
     * Finds all documents associated with a specific category ID.
     *
     * @param categoryId ID of the target category
     * @return List of matching documents
     */
    List<Document> findByCategoryId(Long categoryId);
}