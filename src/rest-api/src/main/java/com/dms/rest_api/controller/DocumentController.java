package com.dms.rest_api.controller;

import com.dms.rest_api.entity.Document;
import com.dms.rest_api.repository.DocumentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST Controller responsible for exposing HTTP endpoints for document management.
 * 
 * Maps requests arriving at '/api/documents' to specific handler methods.
 */
@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentRepository documentRepository;

    /**
     * Constructor injection for the DocumentRepository.
     * Preferred over @Autowired on fields to enable immutability and easier unit testing.
     */
    @Autowired
    public DocumentController(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    /**
     * Retrieves all documents, optionally filtered by a specific category ID.
     * 
     * @param categoryId Optional category ID to filter documents by.
     * @return 200 OK with the list of Document entities.
     */
    @GetMapping
    public ResponseEntity<List<Document>> getAllDocuments(@RequestParam(required = false) Long categoryId) {
        if (categoryId != null) {
            return ResponseEntity.ok(documentRepository.findByCategoryId(categoryId));
        }
        return ResponseEntity.ok(documentRepository.findAll());
    }

    /**
     * Retrieves a single document by its ID.
     * 
     * @param id The ID of the document to find.
     * @return 200 OK if found, or 404 NOT FOUND if the document does not exist.
     */
    @GetMapping("/{id}")
    public ResponseEntity<Document> getDocumentById(@PathVariable Long id) {
        return documentRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Creates and persists a new document in the database.
     * 
     * @param document The document payload received in the HTTP request body.
     * @return 201 CREATED with the newly saved Document entity.
     */
    @PostMapping
    public ResponseEntity<Document> createDocument(@RequestBody Document document) {
        Document savedDocument = documentRepository.save(document);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedDocument);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Document> updateDocument(@PathVariable Long id, @RequestBody Document updatedDocument) {
        return documentRepository.findById(id)
            .map(existingDoc -> {
                existingDoc.setTitle(updatedDocument.getTitle());
                existingDoc.setContent(updatedDocument.getContent());
                existingDoc.setSummary(updatedDocument.getSummary());
                existingDoc.setCategory(updatedDocument.getCategory());
                
                Document saved = documentRepository.save(existingDoc);
                return ResponseEntity.ok(saved);
            })
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Deletes a document by its ID.
     * 
     * @param id The ID of the document to delete.
     * @return 204 NO CONTENT if successfully deleted, or 404 NOT FOUND if not present.
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDocument(@PathVariable Long id) {
        if (!documentRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        documentRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}