package com.dms.rest_api.controller;

import com.dms.rest_api.entity.Category;
import com.dms.rest_api.repository.CategoryRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

@WebMvcTest(CategoryController.class)
class CategoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private CategoryRepository categoryRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private Category sampleCategory;

    @BeforeEach
    void setUp() {
        sampleCategory = Category.builder()
                .id(1L)
                .name("Contracts")
                .build();
    }

    @Test
    @DisplayName("GET /api/categories - Should return all categories")
    void getAllCategories_ShouldReturnList() throws Exception {
        when(categoryRepository.findAll()).thenReturn(Arrays.asList(sampleCategory));

        mockMvc.perform(get("/api/categories"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].name", is("Contracts")));

        verify(categoryRepository, times(1)).findAll();
    }

    @Test
    @DisplayName("POST /api/categories - Should create new category and return it")
    void createCategory_ShouldReturnSavedCategory() throws Exception {
        Category inputCategory = Category.builder().name("Invoices").build();
        Category savedCategory = Category.builder().id(2L).name("Invoices").build();

        when(categoryRepository.save(any(Category.class))).thenReturn(savedCategory);

        mockMvc.perform(post("/api/categories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(inputCategory)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", is(2)))
                .andExpect(jsonPath("$.name", is("Invoices")));

        verify(categoryRepository, times(1)).save(any(Category.class));
    }

    @Test
    @DisplayName("DELETE /api/categories/{id} - Should delete category when exists")
    void deleteCategory_WhenExists_ShouldReturn204() throws Exception {
        when(categoryRepository.existsById(1L)).thenReturn(true);
        doNothing().when(categoryRepository).deleteById(1L);

        mockMvc.perform(delete("/api/categories/1"))
                .andExpect(status().isNoContent());

        verify(categoryRepository, times(1)).existsById(1L);
        verify(categoryRepository, times(1)).deleteById(1L);
    }
}