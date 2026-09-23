package com.dms.rest_api.service;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.exception.ResourceNotFoundException;
import com.dms.rest_api.mapper.CategoryMapper;
import com.dms.rest_api.repository.CategoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Service handling business logic for category administration.
 */
@Service
@Transactional
public class CategoryService {

    private final CategoryRepository categoryRepository;
    private final CategoryMapper categoryMapper;

    // Constructor injection preferred over @Autowired
    public CategoryService(CategoryRepository categoryRepository, CategoryMapper categoryMapper) {
        this.categoryRepository = categoryRepository;
        this.categoryMapper = categoryMapper;
    }

    /**
     * Retrieves all categories.
     */
    @Transactional(readOnly = true)
    public List<CategoryResponseDto> findAll() {
        return categoryRepository.findAll().stream()
                .map(categoryMapper::toDto)
                .collect(Collectors.toList());
    }

    /**
     * Fetches a Category DTO by ID for Controller endpoints.
     * Throws ResourceNotFoundException if ID is null or does not exist.
     */
    @Transactional(readOnly = true)
    public CategoryResponseDto findById(Long categoryId) {
        if (categoryId == null) {
            throw new ResourceNotFoundException("Category ID must not be null");
        }
        return categoryMapper.toDto(findEntityById(categoryId));
    }

    /**
     * Helper method to fetch the internal Category entity.
     * Can be used by this service or cross-service (e.g. DocumentService).
     */
    @Transactional(readOnly = true)
    public Category findEntityById(Long categoryId) {
        if (categoryId == null) {
            return null;
        }
        return categoryRepository.findById(categoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found with ID: " + categoryId));
    }

    /**
     * Creates a new category.
     */
    public CategoryResponseDto create(CategoryRequestDto dto) {
        Category category = categoryMapper.toEntity(dto);
        return categoryMapper.toDto(categoryRepository.save(category));
    }

    /**
     * Updates an existing category by its ID.
     */
    public CategoryResponseDto update(Long id, CategoryRequestDto dto) {
        Category category = findEntityById(id);
        categoryMapper.updateEntityFromDto(dto, category);
        return categoryMapper.toDto(categoryRepository.save(category));
    }

    /**
     * Deletes a category by its ID.
     */
    public void delete(Long id) {
        if (!categoryRepository.existsById(id)) {
            throw new ResourceNotFoundException("Category not found with ID: " + id);
        }
        categoryRepository.deleteById(id);
    }
}