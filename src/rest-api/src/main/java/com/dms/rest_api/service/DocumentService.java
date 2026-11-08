package com.dms.rest_api.service;

import com.dms.rest_api.config.RabbitConfig;
import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.dto.OcrMessageDto;
import com.dms.rest_api.dto.OcrResultDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import com.dms.rest_api.exception.MessagingException;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.logging.LogSanitizer;
import com.dms.rest_api.mapper.DocumentMapper;
import com.dms.rest_api.repository.DocumentRepository;

import lombok.extern.slf4j.Slf4j;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Service
@Transactional
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final CategoryService categoryService;    
    private final DocumentMapper documentMapper;
    private final ObjectStorageService objectStorageService;
    private final RabbitTemplate rabbitTemplate;
    private final SearchService searchService;

    public DocumentService(DocumentRepository documentRepository,
                           CategoryService categoryService,
                           DocumentMapper documentMapper,
                           ObjectStorageService objectStorageService,
                           RabbitTemplate rabbitTemplate,
                           SearchService searchService) {
        this.documentRepository = documentRepository;
        this.categoryService = categoryService;
        this.documentMapper = documentMapper;
        this.objectStorageService = objectStorageService;
        this.rabbitTemplate = rabbitTemplate;
        this.searchService = searchService;
    }

    @Transactional(readOnly = true)
    public List<DocumentResponseDto> findAll(Long categoryId) {
        List<Document> docs = (categoryId != null)
                ? documentRepository.findByCategoryId(categoryId)
                : documentRepository.findAll();
        log.debug("Found {} documents (categoryId={})", docs.size(), categoryId);

        return docs.stream()
                .map(documentMapper::toDto)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<DocumentResponseDto> search(String query) {
        if (query == null || query.isBlank()) {
            throw new IllegalArgumentException("Search term must not be empty");
        }
        List<Long> ids = searchService.searchDocumentIds(query.trim());
        Map<Long, Document> byId = documentRepository.findAllById(ids).stream()
                .collect(Collectors.toMap(Document::getId, Function.identity()));
        List<DocumentResponseDto> result = ids.stream()
                .map(byId::get)
                .filter(Objects::nonNull)
                .map(documentMapper::toDto)
                .toList();
        log.info("Search for '{}' found {} documents", LogSanitizer.sanitize(query), result.size());
        return result;
    }

    @Transactional(readOnly = true)
    public DocumentResponseDto findById(Long id) {
        return documentRepository.findById(id)
                .map(documentMapper::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));
    }

    public DocumentResponseDto storeFile(MultipartFile file, String title, Long categoryId) {
        String rawFilename = objectStorageService.sanitizeFilename(file.getOriginalFilename());
        log.info("Upload received: file='{}', size={} bytes, type={}, categoryId={}",
                LogSanitizer.sanitize(rawFilename), file.getSize(),
                LogSanitizer.sanitize(file.getContentType()), categoryId);
        String objectKey = objectStorageService.store(file);

        try {
            Category category = categoryService.findEntityById(categoryId);

            Document document = Document.builder()
                    .title(title != null && !title.isBlank() ? title : rawFilename)
                    .originalFileName(rawFilename)
                    .fileType(file.getContentType())
                    .fileSize(file.getSize())
                    .storagePath(objectKey)
                    .status(Document.DocumentStatus.PENDING)
                    .category(category)
                    .build();

            Document savedDocument = documentRepository.save(document);

            try {
                OcrMessageDto message = new OcrMessageDto(savedDocument.getId(), objectStorageService.getBucket(), objectKey);
                rabbitTemplate.convertAndSend(RabbitConfig.OCR_QUEUE, message);
                log.info("Successfully sent OCR message for document ID: {} to queue: {}", savedDocument.getId(), RabbitConfig.OCR_QUEUE);
            } catch (Exception ex) {
                log.error("Failed to send message to RabbitMQ for document ID: {}", savedDocument.getId(), ex);
                throw new MessagingException("Messaging layer error: Could not dispatch OCR task", ex);
            }

            return documentMapper.toDto(savedDocument);
        } catch (Exception ex) {
            // Remove the stored object again if saving or messaging fails
            log.error("Saving metadata for '{}' failed, removing stored file again",
                    LogSanitizer.sanitize(rawFilename), ex);
            objectStorageService.deleteQuietly(objectKey);
            throw ex;
        }
    }

    @Transactional(readOnly = true)
    public Resource loadFileAsResource(Long id) {
        Document doc = documentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));

        return objectStorageService.load(doc.getStoragePath());
    }

    public DocumentResponseDto updateDocument(Long id, DocumentUpdateDto dto) {
        Document existing = documentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));

        documentMapper.updateEntityFromDto(dto, existing);

        if (Boolean.TRUE.equals(dto.getClearCategory())) {
            existing.setCategory(null);
        } else if (dto.getCategoryId() != null) {
            existing.setCategory(categoryService.findEntityById(dto.getCategoryId()));
        }

        Document saved = documentRepository.save(existing);
        log.info("Document {} updated", id);
        return documentMapper.toDto(saved);
    }

    public void deleteDocument(Long id) {
        Document doc = documentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));

        objectStorageService.deleteQuietly(doc.getStoragePath());
        documentRepository.delete(doc);
        log.info("Document {} deleted", id);
    }

    @RabbitListener(queues = RabbitConfig.OCR_RESULT_QUEUE)
    public void applyOcrResult(OcrResultDto result) {
        documentRepository.findById(result.documentId()).ifPresentOrElse(doc -> {
            doc.setStatus(result.status());
            if (result.content() != null) {
                doc.setContent(result.content());
            }
            documentRepository.save(doc);
            log.info("OCR result for document {} applied: status={}", doc.getId(), result.status());
        }, () -> log.warn("OCR result for unknown document {} ignored (deleted in the meantime?)", result.documentId()));
    }

}