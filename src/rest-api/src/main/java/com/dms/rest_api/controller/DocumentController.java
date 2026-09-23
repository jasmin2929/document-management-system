package com.dms.rest_api.controller;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.service.DocumentService;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * REST Controller exposing API endpoints for document creation, downloading, updating, and deletion.
 */
@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @GetMapping
    public ResponseEntity<List<DocumentResponseDto>> getAllDocuments(@RequestParam(required = false) Long categoryId) {
        return ResponseEntity.ok(documentService.findAll(categoryId));
    }

    @GetMapping("/{id}")
    public ResponseEntity<DocumentResponseDto> getDocumentById(@PathVariable Long id) {
        return ResponseEntity.ok(documentService.findById(id));
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentResponseDto> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "title", required = false) String title,
            @RequestParam(value = "categoryId", required = false) Long categoryId) {

        DocumentResponseDto dto = documentService.storeFile(file, title, categoryId);
        return ResponseEntity.status(HttpStatus.CREATED).body(dto);
    }

    @GetMapping("/{id}/file")
    public ResponseEntity<Resource> downloadFile(@PathVariable Long id) {
        DocumentResponseDto doc = documentService.findById(id);
        Resource resource = documentService.loadFileAsResource(id);

        String contentType = doc.getFileType() != null ? doc.getFileType() : "application/octet-stream";

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + doc.getOriginalFileName() + "\"")
                .body(resource);
    }

    @PutMapping("/{id}")
    public ResponseEntity<DocumentResponseDto> updateDocument(@PathVariable Long id, @RequestBody DocumentUpdateDto dto) {
        return ResponseEntity.ok(documentService.updateDocument(id, dto));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDocument(@PathVariable Long id) {
        documentService.deleteDocument(id);
        return ResponseEntity.noContent().build();
    }
}