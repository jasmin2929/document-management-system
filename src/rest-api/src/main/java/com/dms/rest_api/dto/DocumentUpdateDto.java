package com.dms.rest_api.dto;

import com.dms.rest_api.entity.Document.DocumentStatus;
import lombok.Data;

/**
 * Data Transfer Object for updating document attributes.
 * Excludes immutable/server-controlled metadata like fileSize, originalFileName, or uploadDate.
 */
@Data
public class DocumentUpdateDto {

    private String title;
    private String content;
    private String summary;
    private DocumentStatus status;
    private Long categoryId;
}