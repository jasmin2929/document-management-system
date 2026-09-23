package com.dms.rest_api.controller;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.service.CategoryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.BDDMockito.willDoNothing;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(CategoryController.class)
class CategoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private CategoryService categoryService;

    @Test
    @DisplayName("GET /api/categories - Returns list of categories")
    void getAllCategories_ReturnsOk() throws Exception {
        CategoryResponseDto responseDto = CategoryResponseDto.builder()
                .id(10L)
                .name("Finance")
                .build();

        given(categoryService.findAll()).willReturn(List.of(responseDto));

        mockMvc.perform(get("/api/categories"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("Finance"));
    }

    @Test
    @DisplayName("POST /api/categories - Creates category with valid DTO")
    void createCategory_ValidPayload_ReturnsCreated() throws Exception {
        CategoryRequestDto requestDto = new CategoryRequestDto();
        requestDto.setName("Finance");

        CategoryResponseDto responseDto = CategoryResponseDto.builder()
                .id(10L)
                .name("Finance")
                .build();

        given(categoryService.create(any(CategoryRequestDto.class))).willReturn(responseDto);

        mockMvc.perform(post("/api/categories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestDto)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(10L));
    }

    @Test
    @DisplayName("PUT /api/categories/{id} - Updates category successfully")
    void updateCategory_ValidPayload_ReturnsOk() throws Exception {
        CategoryRequestDto requestDto = new CategoryRequestDto();
        requestDto.setName("Updated Finance");

        CategoryResponseDto responseDto = CategoryResponseDto.builder()
                .id(10L)
                .name("Updated Finance")
                .build();

        given(categoryService.update(eq(10L), any(CategoryRequestDto.class))).willReturn(responseDto);

        mockMvc.perform(put("/api/categories/10")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestDto)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated Finance"));
    }

    @Test
    @DisplayName("DELETE /api/categories/{id} - Deletes category successfully")
    void deleteCategory_Success_ReturnsNoContent() throws Exception {
        // Arrange
        Long categoryId = 10L;
        willDoNothing().given(categoryService).delete(categoryId);

        // Act & Assert
        mockMvc.perform(delete("/api/categories/{id}", categoryId))
                .andExpect(status().isNoContent()); // Oder isOk(), je nach Controller-Implementierung

        verify(categoryService, times(1)).delete(categoryId);
    }

    @Test
    @DisplayName("GET /api/categories/{id} - Returns category when exists")
    void getCategoryById_Success_ReturnsOk() throws Exception {
        // Arrange
        CategoryResponseDto responseDto = CategoryResponseDto.builder()
                .id(10L)
                .name("Finance")
                .build();

        given(categoryService.findById(10L)).willReturn(responseDto);

        // Act & Assert
        mockMvc.perform(get("/api/categories/10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(10L))
                .andExpect(jsonPath("$.name").value("Finance"));
    }

}