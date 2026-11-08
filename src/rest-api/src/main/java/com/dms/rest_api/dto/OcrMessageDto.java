package com.dms.rest_api.dto;

/** OCR queue message: {"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/<uuid>.pdf"} */
public record OcrMessageDto(Long documentId, String bucket, String objectKey) {
}
