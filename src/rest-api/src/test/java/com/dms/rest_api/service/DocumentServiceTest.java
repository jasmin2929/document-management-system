package com.dms.rest_api.service;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
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
import org.springframework.core.io.Resource;
import org.springframework.mock.web.MockMultipartFile;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
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
    private FileStorageService fileStorageService;

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
                .storagePath("/app/uploads/uuid_Invoice_2026.pdf")
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
            Path targetPath = Paths.get("/app/uploads/uuid_test.pdf");

            given(fileStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(fileStorageService.store(mockFile)).willReturn(targetPath);
            given(categoryService.findEntityById(10L)).willReturn(sampleCategory);
            given(documentRepository.save(any(Document.class))).willReturn(sampleDocument);
            given(documentMapper.toDto(sampleDocument)).willReturn(sampleResponseDto);

            DocumentResponseDto result = documentService.storeFile(mockFile, "My Title", 10L);

            assertThat(result).isNotNull();
            verify(fileStorageService, times(1)).store(mockFile);
            verify(documentRepository, times(1)).save(any(Document.class));
            verify(fileStorageService, never()).deleteQuietly(any());
        }

        @Test
        @DisplayName("storeFile() cleans up physical file on rollback when DB persistence fails")
        void storeFile_DbFailure_RollsBackPhysicalFile() {
            MockMultipartFile mockFile = new MockMultipartFile("file", "test.pdf", "application/pdf", "dummy data".getBytes());
            Path targetPath = Paths.get("/app/uploads/uuid_test.pdf");

            given(fileStorageService.sanitizeFilename("test.pdf")).willReturn("test.pdf");
            given(fileStorageService.store(mockFile)).willReturn(targetPath);
            given(categoryService.findEntityById(10L)).willReturn(sampleCategory);
            given(documentRepository.save(any(Document.class))).willThrow(new RuntimeException("Database error"));

            assertThatThrownBy(() -> documentService.storeFile(mockFile, "Title", 10L))
                    .isInstanceOf(RuntimeException.class)
                    .hasMessage("Database error");

            verify(fileStorageService, times(1)).deleteQuietly(targetPath);
        }
    }

    @Nested
    @DisplayName("Load & Update & Delete Tests")
    class ResourceUpdateDeleteTests {

        @Test
        @DisplayName("loadFileAsResource() delegates to FileStorageService")
        void loadFileAsResource_Success_ReturnsResource() {
            Resource mockResource = mock(Resource.class);
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));
            given(fileStorageService.loadAsResource(sampleDocument.getStoragePath())).willReturn(mockResource);

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
        @DisplayName("deleteDocument() removes physical file and deletes database record")
        void deleteDocument_Success_DeletesFileAndDbRecord() {
            given(documentRepository.findById(1L)).willReturn(Optional.of(sampleDocument));

            documentService.deleteDocument(1L);

            verify(fileStorageService, times(1)).deleteQuietly(Paths.get(sampleDocument.getStoragePath()));
            verify(documentRepository, times(1)).delete(sampleDocument);
        }
    }
}