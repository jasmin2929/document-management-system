package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.entity.Document;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

/**
 * MapStruct mapper for converting between Document entities and DTOs.
 * Reuses CategoryMapper to transform embedded Category relationships.
 */
@Mapper(componentModel = "spring", uses = {CategoryMapper.class})
public interface DocumentMapper {

    DocumentResponseDto toDto(Document document);

    /**
     * Performs an in-place update of an existing entity from a update DTO.
     * Ignores null fields in the DTO to preserve existing entity values (partial update).
     */
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntityFromDto(DocumentUpdateDto dto, @MappingTarget Document entity);
}