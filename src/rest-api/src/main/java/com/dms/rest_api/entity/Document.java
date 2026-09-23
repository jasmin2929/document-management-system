package com.dms.rest_api.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

/**
 * Entity representing a managed document along with its file metadata and processing state.
 */
@Entity
@Table(name = "documents")
@Getter
@Setter
// Exclude parent entity from Lombok toString and equals/hashCode to prevent cyclic loops
@ToString(exclude = "category")
@EqualsAndHashCode(exclude = "category")
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Document {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(columnDefinition = "TEXT")
    private String summary;

    private String originalFileName;
    private String fileType;
    private Long fileSize;
    private String storagePath;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private DocumentStatus status = DocumentStatus.PENDING;

    @Builder.Default
    private LocalDateTime uploadDate = LocalDateTime.now();

    private LocalDateTime lastModifiedDate;

    /**
     * Many-To-One relationship to the parent category.
     * Uses LAZY fetching to prevent unnecessary database queries when loading documents.
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    /**
     * JPA Lifecycle Hook to automatically track entity update timestamps.
     */
    @PreUpdate
    public void preUpdate() {
        this.lastModifiedDate = LocalDateTime.now();
    }

    /**
     * Processing status lifecycle of the document within the DMS.
     */
    public enum DocumentStatus {
        PENDING,
        PROCESSING,
        PROCESSED,
        FAILED
    }
}