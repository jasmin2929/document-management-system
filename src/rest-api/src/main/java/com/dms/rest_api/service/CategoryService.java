package com.dms.rest_api.service;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.mapper.CategoryMapper;
import com.dms.rest_api.logging.LogSanitizer;
import com.dms.rest_api.repository.CategoryRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@Transactional
public class CategoryService {

    private final CategoryRepository categoryRepository;
    private final CategoryMapper categoryMapper;

    public CategoryService(CategoryRepository categoryRepository, CategoryMapper categoryMapper) {
        this.categoryRepository = categoryRepository;
        this.categoryMapper = categoryMapper;
    }

    @Transactional(readOnly = true)
    public List<CategoryResponseDto> findAll() {
        return categoryRepository.findAll().stream()
                .map(categoryMapper::toDto)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public CategoryResponseDto findById(Long categoryId) {
        if (categoryId == null) {
            throw new ResourceNotFoundException("Category ID must not be null");
        }
        return categoryMapper.toDto(findEntityById(categoryId));
    }

    @Transactional(readOnly = true)
    public Category findEntityById(Long categoryId) {
        if (categoryId == null) {
            return null;
        }
        return categoryRepository.findById(categoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found with ID: " + categoryId));
    }

    public CategoryResponseDto create(CategoryRequestDto dto) {
        Category category = categoryRepository.save(categoryMapper.toEntity(dto));
        log.info("Category {} created: '{}'", category.getId(), LogSanitizer.sanitize(category.getName()));
        return categoryMapper.toDto(category);
    }

    public CategoryResponseDto update(Long id, CategoryRequestDto dto) {
        Category category = findEntityById(id);
        categoryMapper.updateEntityFromDto(dto, category);
        Category saved = categoryRepository.save(category);
        log.info("Category {} renamed to '{}'", id, LogSanitizer.sanitize(saved.getName()));
        return categoryMapper.toDto(saved);
    }

    public void delete(Long id) {
        if (!categoryRepository.existsById(id)) {
            throw new ResourceNotFoundException("Category not found with ID: " + id);
        }
        categoryRepository.deleteById(id);
        // Category.documents uses CascadeType.ALL, so its documents are deleted as well
        log.warn("Category {} deleted together with all of its documents", id);
    }
}