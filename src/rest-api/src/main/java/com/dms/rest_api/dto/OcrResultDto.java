package com.dms.rest_api.dto;

import com.dms.rest_api.entity.Document.DocumentStatus;

/** Result from the OCR worker: {"documentId": 5, "status": "PROCESSED", "content": "..."}; FAILED has no content. */
public record OcrResultDto(Long documentId, DocumentStatus status, String content) {
}
