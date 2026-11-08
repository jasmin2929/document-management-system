package com.dms.rest_api.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "documents")
@Getter
@Setter
// bidirectional relation: including it would recurse endlessly
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

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    @PreUpdate
    public void preUpdate() {
        this.lastModifiedDate = LocalDateTime.now();
    }

    public enum DocumentStatus {
        PENDING,
        PROCESSING,
        PROCESSED,
        FAILED
    }
}