package com.dms.rest_api.service;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.dto.OcrMessageDto;
import com.dms.rest_api.dto.OcrResultDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import com.dms.rest_api.exception.MessagingException;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.mapper.DocumentMapper;
import com.dms.rest_api.repository.DocumentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.amqp.AmqpException;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.core.io.Resource;
import org.springframework.mock.web.MockMultipartFile;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DocumentServiceTest {

    @Mock
    private DocumentRepository documentRepository;

    @Mock
    private CategoryService categoryService;

    @Mock
    private DocumentMapper documentMapper;

    @Mock
    private ObjectStorageService objectStorageService;

    @Mock
    private RabbitTemplate rabbitTemplate;

    @Mock
    private SearchService searchService;

    @InjectMocks
    private DocumentService documentService;

    private Document sampleDocument;
    private DocumentResponseDto sampleResponseDto;
    private Category sampleCategory;

    @BeforeEach
    void setUp() {
        sampleCategory = Category.builder().id(10L).name("Invoices").build();

        sampleDocument = Document.builder()
                .id(1L)
                .title("Invoice_2026.pdf")
                .originalFileName("Invoice_2026.pdf")
                .fileType("application/pdf")
                .fileSize(1024L)
                .storagePath("documents/uuid.pdf")
                .status(Document.DocumentStatus.PROCESSED)
                .category(sampleCategory)
                .build();

        sampleResponseDto = DocumentResponseDto.builder()
                .id(1L)
                .title("Invoice_2026.pdf")
                .originalFileName("Invoice_2026.pdf")
                .fileType("application/pdf")
                .fileSize(1024L)
                .status(Document.DocumentStatus.PROCESSED)
                .build();
    }

    @Nested
    @DisplayName("Find Methods Tests")
    class FindTests {

        @Test
        @DisplayName("findAll() without category ID should return all documents")
        void findAll_WithoutCategory_ReturnsAllDocuments() {
            given(documentRepository.findAll()).willReturn(List.of(sampleDocument));
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            List<DocumentResponseDto> result = documentService.findAll(null);

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getId()).isEqualTo(1L);
            verify(documentRepository, times(1)).findAll();
            verify(documentRepository, never()).findByCategoryId(anyLong());
        }

        @Test
        @DisplayName("findAll() with category ID should call findByCategoryId()")
        void findAll_WithCategory_ReturnsFilteredDocuments() {
            given(documentRepository.findByCategoryId(10L)).willReturn(List.of(sampleDocument));
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            List<DocumentResponseDto> result = documentService.findAll(10L);

            assertThat(result).hasSize(1);
            verify(documentRepository, times(1)).findByCategoryId(10L);
            verify(documentRepository, never()).findAll();
        }

        @Test
        @DisplayName("findById() with existing ID should return DocumentDto")
        void findById_ExistingId_ReturnsDocumentDto() {
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            DocumentResponseDto result = documentService.findById(1L);

            assertThat(result).isNotNull();
            assertThat(result.getId()).isEqualTo(1L);
        }

        @Test
        @DisplayName("findById() with non-existing ID should throw ResourceNotFoundException")
        void findById_NonExistingId_ThrowsException() {
            given(documentRepository.findById(99L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> documentService.findById(99L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("Document not found with ID: 99");
        }
    }

    @Nested
    @DisplayName("Store File Tests")
    class StoreFileTests {

        @Test
        @DisplayName("storeFile() successfully stores file and creates metadata entity")
        void storeFile_Success_ReturnsResponseDto() {
            MockMultipartFile mockFile = new MockMultipartFile("file", "test.pdf", "application/pdf", "dummy data".getBytes());
            String objectKey = "documents/uuid.pdf";

            given(objectStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(objectStorageService.store(mockFile)).willReturn(objectKey);
            given(categoryService.findEntityById(10L)).willReturn(sampleCategory);
            given(documentRepository.save(any(Document.class))).willReturn(sampleDocument);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            DocumentResponseDto result = documentService.storeFile(mockFile, "My Title", 10L);

            assertThat(result).isNotNull();
            verify(objectStorageService, times(1)).store(mockFile);
            verify(documentRepository, times(1)).save(any(Document.class));
            verify(objectStorageService, never()).deleteQuietly(any());
        }

        @Test
        @DisplayName("storeFile() saves the object key as storage path and sends it to the OCR queue")
        void storeFile_Success_SendsObjectKeyToOcrQueue() {
            MockMultipartFile mockFile = new MockMultipartFile("file", "test.pdf", "application/pdf", "dummy data".getBytes());
            String objectKey = "documents/uuid.pdf";

            given(objectStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(objectStorageService.store(mockFile)).willReturn(objectKey);
            given(objectStorageService.getBucket()).willReturn("dms-documents");
            given(documentRepository.save(any(Document.class))).willReturn(sampleDocument);

            documentService.storeFile(mockFile, null, null);

            verify(documentRepository).save(argThat(doc -> objectKey.equals(doc.getStoragePath())));
            verify(rabbitTemplate).convertAndSend(eq("ocr-queue"),
                    eq(new OcrMessageDto(sampleDocument.getId(), "dms-documents", objectKey)));
        }

        @Test
        @DisplayName("storeFile() removes the stored object when the OCR message cannot be sent")
        void storeFile_MessagingFailure_RollsBackStoredObject() {
            MockMultipartFile mockFile = new MockMultipartFile("file", "test.pdf", "application/pdf", "dummy data".getBytes());
            String objectKey = "documents/uuid.pdf";

            given(objectStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(objectStorageService.store(mockFile)).willReturn(objectKey);
            given(documentRepository.save(any(Document.class))).willReturn(sampleDocument);
            doThrow(new AmqpException("broker down")).when(rabbitTemplate).convertAndSend(anyString(), any(Object.class));

            assertThatThrownBy(() -> documentService.storeFile(mockFile, null, null))
                    .isInstanceOf(MessagingException.class);

            verify(objectStorageService, times(1)).deleteQuietly(objectKey);
        }

        @Test
        @DisplayName("storeFile() removes the stored object again when DB persistence fails")
        void storeFile_DbFailure_RollsBackPhysicalFile() {
            MockMultipartFile mockFile = new MockMultipartFile("file", "test.pdf", "application/pdf", "dummy data".getBytes());
            String objectKey = "documents/uuid.pdf";

            given(objectStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(objectStorageService.store(mockFile)).willReturn(objectKey);
            given(categoryService.findEntityById(10L)).willReturn(sampleCategory);
            given(documentRepository.save(any(Document.class))).willThrow(new RuntimeException("Database error"));

            assertThatThrownBy(() -> documentService.storeFile(mockFile, "Title", 10L))
                    .isInstanceOf(RuntimeException.class)
                    .hasMessage("Database error");

            verify(objectStorageService, times(1)).deleteQuietly(objectKey);
        }
    }

    @Nested
    @DisplayName("Load & Update & Delete Tests")
    class ResourceUpdateDeleteTests {

        @Test
        @DisplayName("loadFileAsResource() delegates to ObjectStorageService")
        void loadFileAsResource_Success_ReturnsResource() {
            Resource mockResource = mock(Resource.class);
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(objectStorageService.load(sampleDocument.getStoragePath())).willReturn(mockResource);

            Resource result = documentService.loadFileAsResource(1L);

            assertThat(result).isEqualTo(mockResource);
        }

        @Test
        @DisplayName("updateDocument() updates metadata and returns updated DTO")
        void updateDocument_Success_ReturnsUpdatedDto() {
            DocumentUpdateDto updateDto = new DocumentUpdateDto();
            updateDto.setCategoryId(10L);

            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(categoryService.findEntityById(10L)).willReturn(sampleCategory);
            given(documentRepository.save(sampleDocument)).willReturn(sampleDocument);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            DocumentResponseDto result = documentService.updateDocument(1L, updateDto);

            assertThat(result).isNotNull();
            verify(documentMapper, times(1)).updateEntityFromDto(updateDto, sampleDocument);
            verify(documentRepository, times(1)).save(sampleDocument);
        }

        @Test
        @DisplayName("updateDocument() with clearCategory removes the category")
        void updateDocument_ClearCategory_RemovesCategory() {
            DocumentUpdateDto updateDto = new DocumentUpdateDto();
            updateDto.setClearCategory(true);

            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(documentRepository.save(sampleDocument)).willReturn(sampleDocument);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            documentService.updateDocument(1L, updateDto);

            assertThat(sampleDocument.getCategory()).isNull();
            verify(categoryService, never()).findEntityById(anyLong());
        }

        @Test
        @DisplayName("updateDocument() without categoryId keeps the existing category")
        void updateDocument_NoCategoryId_KeepsCategory() {
            DocumentUpdateDto updateDto = new DocumentUpdateDto();
            updateDto.setTitle("Renamed");

            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(documentRepository.save(sampleDocument)).willReturn(sampleDocument);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            documentService.updateDocument(1L, updateDto);

            assertThat(sampleDocument.getCategory()).isEqualTo(sampleCategory);
        }

        @Test
        @DisplayName("deleteDocument() removes stored object and deletes database record")
        void deleteDocument_Success_DeletesFileAndDbRecord() {
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));

            documentService.deleteDocument(1L);

            verify(objectStorageService, times(1)).deleteQuietly(sampleDocument.getStoragePath());
            verify(documentRepository, times(1)).delete(sampleDocument);
        }
    }

    @Nested
    @DisplayName("applyOcrResult()")
    class OcrResultTests {

        @Test
        @DisplayName("PROCESSED result sets status and stores the recognized text")
        void processedResult_UpdatesStatusAndContent() {
            sampleDocument.setStatus(Document.DocumentStatus.PENDING);
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));

            documentService.applyOcrResult(new OcrResultDto(1L, Document.DocumentStatus.PROCESSED, "Hello World"));

            assertThat(sampleDocument.getStatus()).isEqualTo(Document.DocumentStatus.PROCESSED);
            assertThat(sampleDocument.getContent()).isEqualTo("Hello World");
            verify(documentRepository).save(sampleDocument);
        }

        @Test
        @DisplayName("FAILED result without content keeps the existing content")
        void failedResult_KeepsContent() {
            sampleDocument.setContent("old text");
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));

            documentService.applyOcrResult(new OcrResultDto(1L, Document.DocumentStatus.FAILED, null));

            assertThat(sampleDocument.getStatus()).isEqualTo(Document.DocumentStatus.FAILED);
            assertThat(sampleDocument.getContent()).isEqualTo("old text");
        }

        @Test
        @DisplayName("result for a deleted document is ignored without error")
        void unknownDocument_IsIgnored() {
            given(documentRepository.findById(99L)).willReturn(Optional.empty());

            documentService.applyOcrResult(new OcrResultDto(99L, Document.DocumentStatus.PROCESSED, "text"));

            verify(documentRepository, never()).save(any());
        }
    }

    @Nested
    @DisplayName("search()")
    class SearchTests {

        @Test
        @DisplayName("returns the matching documents in Elasticsearch's relevance order, skipping deleted ones")
        void search_KeepsRelevanceOrder() {
            Document second = Document.builder().id(2L).title("Second.pdf").build();
            DocumentResponseDto secondDto = DocumentResponseDto.builder().id(2L).title("Second.pdf").build();
            given(searchService.searchDocumentIds("hello")).willReturn(List.of(2L, 99L, 1L));
            given(documentRepository.findAllById(List.of(2L, 99L, 1L))).willReturn(List.of(sampleDocument, second));
            given(documentMapper.toDto(second)).willReturn(secondDto);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            assertThat(documentService.search(" hello ")).containsExactly(secondDto, sampleResponseDto);
        }

        @Test
        @DisplayName("blank search term is rejected")
        void search_BlankQuery_Throws() {
            assertThatThrownBy(() -> documentService.search("  ")).isInstanceOf(IllegalArgumentException.class);
            verifyNoInteractions(searchService);
        }
    }
}
