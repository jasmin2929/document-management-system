package com.dms.rest_api.service;

import com.dms.rest_api.config.RabbitConfig;
import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import com.dms.rest_api.exception.MessagingException;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.logging.LogSanitizer;
import com.dms.rest_api.mapper.DocumentMapper;
import com.dms.rest_api.repository.CategoryRepository;
import com.dms.rest_api.repository.DocumentRepository;

import lombok.extern.slf4j.Slf4j;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Orchestrates document lifecycle, business domain rules, and metadata persistence.
 */
@Slf4j
@Service
@Transactional
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final CategoryService categoryService;    
    private final DocumentMapper documentMapper;
    private final FileStorageService fileStorageService;
    private final RabbitTemplate rabbitTemplate;

    public DocumentService(DocumentRepository documentRepository,
                           CategoryService categoryService,
                           DocumentMapper documentMapper,
                           FileStorageService fileStorageService,
                            RabbitTemplate rabbitTemplate) {
        this.documentRepository = documentRepository;
        this.categoryService = categoryService;
        this.documentMapper = documentMapper;
        this.fileStorageService = fileStorageService;
        this.rabbitTemplate = rabbitTemplate;
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
    public DocumentResponseDto findById(Long id) {
        return documentRepository.findById(id)
                .map(documentMapper::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));
    }

    public DocumentResponseDto storeFile(MultipartFile file, String title, Long categoryId) {
        String rawFilename = fileStorageService.sanitizeFilename(file.getOriginalFilename());
        log.info("Upload received: file='{}', size={} bytes, type={}, categoryId={}",
                LogSanitizer.sanitize(rawFilename), file.getSize(),
                LogSanitizer.sanitize(file.getContentType()), categoryId);
        Path targetLocation = fileStorageService.store(file);

        try {
            Category category = categoryService.findEntityById(categoryId);

            Document document = Document.builder()
                    .title(title != null && !title.isBlank() ? title : rawFilename)
                    .originalFileName(rawFilename)
                    .fileType(file.getContentType())
                    .fileSize(file.getSize())
                    .storagePath(targetLocation.toString())
                    .status(Document.DocumentStatus.PENDING)
                    .category(category)
                    .build();

            Document savedDocument = documentRepository.save(document);

            // Send message to RabbitMQ for OCR processing
            try {
                rabbitTemplate.convertAndSend(RabbitConfig.OCR_QUEUE, savedDocument.getId());
                log.info("Successfully sent OCR message for document ID: {} to queue: {}", savedDocument.getId(), RabbitConfig.OCR_QUEUE);
            } catch (Exception ex) {
                log.error("Failed to send message to RabbitMQ for document ID: {}", savedDocument.getId(), ex);
                throw new MessagingException("Messaging layer error: Could not dispatch OCR task", ex);
            }

            return documentMapper.toDto(savedDocument);
        } catch (Exception ex) {
            // Rollback physical file if DB insertion or mapping fails
            log.error("Saving metadata for '{}' failed, removing stored file again",
                    LogSanitizer.sanitize(rawFilename), ex);
            fileStorageService.deleteQuietly(targetLocation);
            throw ex;
        }
    }

    @Transactional(readOnly = true)
    public Resource loadFileAsResource(Long id) {
        Document doc = documentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found with ID: " + id));

        return fileStorageService.loadAsResource(doc.getStoragePath());
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

        if (doc.getStoragePath() != null) {
            fileStorageService.deleteQuietly(Paths.get(doc.getStoragePath()));
        }

        documentRepository.delete(doc);
        log.info("Document {} deleted", id);
    }

}