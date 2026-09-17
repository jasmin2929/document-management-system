package com.dms.rest_api.repository;

import com.dms.rest_api.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Data Access Layer interface for the Document entity.
 * 
 * Extends JpaRepository to inherit full CRUD (Create, Read, Update, Delete) operations,
 * pagination, and sorting out of the box without writing explicit SQL queries.
 */
@Repository
public interface DocumentRepository extends JpaRepository<Document, Long> {
    // Custom database queries (e.g., findByTitle) can be added here if needed.
}