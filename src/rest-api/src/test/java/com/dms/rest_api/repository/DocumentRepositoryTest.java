package com.dms.rest_api.repository;

import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class DocumentRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private DocumentRepository documentRepository;

     @Test
    @DisplayName("Should save and retrieve document by ID")
    void findById_ShouldReturnMatchingDocuments() {
        // Given
        Document doc = Document.builder().title("Invoice.pdf").build();
        Document savedDoc = entityManager.persistAndFlush(doc);

        // When
        Optional<Document> result = documentRepository.findById(savedDoc.getId());

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getTitle()).isEqualTo("Invoice.pdf");
    }

    @Test
    @DisplayName("Should find documents successfully by category ID")
    void findByCategoryId_ShouldReturnMatchingDocuments() {
        // Given
        Category category = Category.builder().name("HR Documents").build();
        entityManager.persistAndFlush(category);

        Document doc1 = Document.builder().title("Arbeitsvertrag.pdf").category(category).build();
        Document doc2 = Document.builder().title("Gehaltsabrechnung.pdf").category(category).build();
        Document doc3 = Document.builder().title("Unrelated.pdf").build();

        entityManager.persist(doc1);
        entityManager.persist(doc2);
        entityManager.persist(doc3);
        entityManager.flush();

        // When
        List<Document> foundDocs = documentRepository.findByCategoryId(category.getId());

        // Then
        assertThat(foundDocs).hasSize(2);
        assertThat(foundDocs).extracting(Document::getTitle)
                .containsExactlyInAnyOrder("Arbeitsvertrag.pdf", "Gehaltsabrechnung.pdf");
    }

    @Test
    @DisplayName("Should return empty list when no documents match category ID")
    void findByCategoryId_ShouldReturnEmptyList_WhenCategoryNotFound() {
        // When
        List<Document> foundDocs = documentRepository.findByCategoryId(999L);

        // Then
        assertThat(foundDocs).isEmpty();
    }

}