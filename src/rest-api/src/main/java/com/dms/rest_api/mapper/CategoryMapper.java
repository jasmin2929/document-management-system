package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.entity.Category;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

/**
 * MapStruct mapper for converting between Category entities and DTOs.
 * Configured as a Spring component for direct dependency injection.
 */
@Mapper(componentModel = "spring")
public interface CategoryMapper {

    CategoryResponseDto toDto(Category category);

    /**
     * Maps incoming request DTO to entity, ignoring auto-generated ID and child collection.
     */
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "documents", ignore = true)
    Category toEntity(CategoryRequestDto dto);

    /**
     * Updates an existing Category entity in-place from request DTO.
     */
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "documents", ignore = true)
    void updateEntityFromDto(CategoryRequestDto dto, @MappingTarget Category entity);
}