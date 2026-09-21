package com.dms.rest_api.controller;

import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import com.dms.rest_api.repository.DocumentRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Optional;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.springframework.test.context.bean.override.mockito.MockitoBean;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(DocumentController.class)
class DocumentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private DocumentRepository documentRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private Document sampleDocument;
    private Category sampleCategory;

    @BeforeEach
    void setUp() {
        sampleCategory = Category.builder()
                .id(1L)
                .name("Invoices")
                .build();

        sampleDocument = Document.builder()
                .id(100L)
                .title("Rechnung_2026.pdf")
                .content("Extracted OCR Content")
                .summary("AI Summary text")
                .uploadDate(LocalDateTime.now())
                .category(sampleCategory)
                .build();
    }

    @Test
    @DisplayName("GET /api/documents - Should return all documents")
    void getAllDocuments_ShouldReturnList() throws Exception {
        when(documentRepository.findAll()).thenReturn(Arrays.asList(sampleDocument));

        mockMvc.perform(get("/api/documents"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].id", is(100)))
                .andExpect(jsonPath("$[0].title", is("Rechnung_2026.pdf")));

        verify(documentRepository, times(1)).findAll();
    }

    @Test
    @DisplayName("GET /api/documents?categoryId=1 - Should filter by category")
    void getAllDocuments_ByCategoryId_ShouldReturnFilteredList() throws Exception {
        when(documentRepository.findByCategoryId(1L)).thenReturn(Arrays.asList(sampleDocument));

        mockMvc.perform(get("/api/documents").param("categoryId", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].title", is("Rechnung_2026.pdf")));

        verify(documentRepository, times(1)).findByCategoryId(1L);
    }

    @Test
    @DisplayName("GET /api/documents/{id} - Should return document when exists")
    void getDocumentById_WhenExists_ShouldReturnDocument() throws Exception {
        when(documentRepository.findById(100L)).thenReturn(Optional.of(sampleDocument));

        mockMvc.perform(get("/api/documents/100"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", is(100)))
                .andExpect(jsonPath("$.title", is("Rechnung_2026.pdf")));

        verify(documentRepository, times(1)).findById(100L);
    }

    @Test
    @DisplayName("GET /api/documents/{id} - Should return 404 when not found")
    void getDocumentById_WhenNotFound_ShouldReturn404() throws Exception {
        when(documentRepository.findById(999L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/documents/999"))
                .andExpect(status().isNotFound());

        verify(documentRepository, times(1)).findById(999L);
    }

    @Test
    @DisplayName("POST /api/documents - Should create new document (201 Created)")
    void createDocument_ShouldReturnCreatedDocument() throws Exception {
        Document newDoc = Document.builder().title("Neuer_Vertrag.pdf").build();
        Document savedDoc = Document.builder().id(101L).title("Neuer_Vertrag.pdf").build();

        when(documentRepository.save(any(Document.class))).thenReturn(savedDoc);

        mockMvc.perform(post("/api/documents")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(newDoc)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", is(101)))
                .andExpect(jsonPath("$.title", is("Neuer_Vertrag.pdf")));

        verify(documentRepository, times(1)).save(any(Document.class));
    }

    @Test
    @DisplayName("PUT /api/documents/{id} - Should update existing document")
    void updateDocument_WhenExists_ShouldReturnUpdated() throws Exception {
        Document updatedInfo = Document.builder()
                .title("Updated_Title.pdf")
                .content("New Content")
                .summary("New Summary")
                .build();

        when(documentRepository.findById(100L)).thenReturn(Optional.of(sampleDocument));
        when(documentRepository.save(any(Document.class))).thenAnswer(invocation -> invocation.getArgument(0));

        mockMvc.perform(put("/api/documents/100")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updatedInfo)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title", is("Updated_Title.pdf")))
                .andExpect(jsonPath("$.content", is("New Content")));

        verify(documentRepository, times(1)).findById(100L);
        verify(documentRepository, times(1)).save(any(Document.class));
    }

    @Test
    @DisplayName("DELETE /api/documents/{id} - Should return 204 No Content when deleting existing document")
    void deleteDocument_WhenExists_ShouldReturn204() throws Exception {
        when(documentRepository.existsById(100L)).thenReturn(true);
        doNothing().when(documentRepository).deleteById(100L);

        mockMvc.perform(delete("/api/documents/100"))
                .andExpect(status().isNoContent());

        verify(documentRepository, times(1)).existsById(100L);
        verify(documentRepository, times(1)).deleteById(100L);
    }
}