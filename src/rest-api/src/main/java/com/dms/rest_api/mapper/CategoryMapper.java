package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.entity.Category;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring")
public interface CategoryMapper {

    CategoryResponseDto toDto(Category category);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "documents", ignore = true)
    Category toEntity(CategoryRequestDto dto);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "documents", ignore = true)
    void updateEntityFromDto(CategoryRequestDto dto, @MappingTarget Category entity);
}