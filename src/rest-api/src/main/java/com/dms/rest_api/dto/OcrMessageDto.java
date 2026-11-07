package com.dms.rest_api.dto;

/**
 * Message sent to the OCR queue after an upload, serialized as JSON:
 * {"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/3f2a...c1b.pdf"}.
 * The OCR worker uses bucket and objectKey to download the file from the object storage.
 */
public record OcrMessageDto(Long documentId, String bucket, String objectKey) {
}
