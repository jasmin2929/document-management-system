package com.dms.rest_api.controller;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.service.DocumentService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.doNothing;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(DocumentController.class)
class DocumentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private DocumentService documentService;

    private DocumentResponseDto sampleDto;

    @BeforeEach
    void setUp() {
        sampleDto = DocumentResponseDto.builder()
                .id(1L)
                .title("Report.pdf")
                .originalFileName("Report.pdf")
                .fileType("application/pdf")
                .fileSize(1024L)
                .build();
    }

    @Test
    @DisplayName("GET /api/documents - Returns list of documents")
    void getAllDocuments_ReturnsOkList() throws Exception {
        given(documentService.findAll(null)).willReturn(List.of(sampleDto));

        mockMvc.perform(get("/api/documents"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.size()").value(1))
                .andExpect(jsonPath("$[0].title").value("Report.pdf"));
    }

    @Test
    @DisplayName("POST /api/documents/upload - Processes multipart fileupload")
    void uploadDocument_ReturnsCreated() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "Report.pdf", "application/pdf", "data".getBytes());

        given(documentService.storeFile(any(), eq("Custom Title"), eq(5L))).willReturn(sampleDto);

        mockMvc.perform(multipart("/api/documents/upload")
                        .file(file)
                        .param("title", "Custom Title")
                        .param("categoryId", "5"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L));
    }

    @Test
    @DisplayName("GET /api/documents/{id}/file - Downloads file with correct headers")
    void downloadFile_ReturnsFileResource() throws Exception {
        Resource resource = new ByteArrayResource("dummy content".getBytes());
        given(documentService.findById(1L)).willReturn(sampleDto);
        given(documentService.loadFileAsResource(1L)).willReturn(resource);

        mockMvc.perform(get("/api/documents/1/file"))
                .andExpect(status().isOk())
                .andExpect(header().string(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"Report.pdf\""))
                .andExpect(content().contentType(MediaType.APPLICATION_PDF));
    }

    @Test
    @DisplayName("PUT /api/documents/{id} - Updates document metadata")
    void updateDocument_ReturnsUpdatedDto() throws Exception {
        DocumentUpdateDto updateDto = new DocumentUpdateDto();
        updateDto.setTitle("New Title");

        given(documentService.updateDocument(eq(1L), any(DocumentUpdateDto.class))).willReturn(sampleDto);

        mockMvc.perform(put("/api/documents/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateDto)))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("DELETE /api/documents/{id} - Deletes document and returns 204 No Content")
    void deleteDocument_ReturnsNoContent() throws Exception {
        doNothing().when(documentService).deleteDocument(1L);

        mockMvc.perform(delete("/api/documents/1"))
                .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("GET /api/documents/{id} - Returns document metadata by ID")
    void getDocumentById_ReturnsOk() throws Exception {
        given(documentService.findById(1L)).willReturn(sampleDto);

        mockMvc.perform(get("/api/documents/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.title").value("Report.pdf"));
    }

    @Test
    @DisplayName("GET /api/documents/{id} - Returns 404 when document not found")
    void getDocumentById_NotFound_Returns404() throws Exception {
        given(documentService.findById(99L)).willThrow(new ResourceNotFoundException("Document not found"));

        mockMvc.perform(get("/api/documents/99"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/documents/upload - Returns 400 when file is missing")
    void uploadDocument_MissingFile_ReturnsBadRequest() throws Exception {
        mockMvc.perform(multipart("/api/documents/upload"))
                .andExpect(status().isBadRequest());
    }
}