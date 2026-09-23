package com.dms.rest_api.dto;

import com.dms.rest_api.entity.Document.DocumentStatus;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Data Transfer Object representing complete document details sent to clients.
 * Decouples API contract from internal database fields like storage path.
 */
@Data
@Builder
public class DocumentResponseDto {

    private Long id;
    private String title;
    private String content;
    private String summary;
    private String originalFileName;
    private String fileType;
    private Long fileSize;
    private DocumentStatus status;
    private LocalDateTime uploadDate;
    private LocalDateTime lastModifiedDate;
    private CategoryResponseDto category;
}