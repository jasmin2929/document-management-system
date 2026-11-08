package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.entity.Document;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring", uses = {CategoryMapper.class})
public interface DocumentMapper {

    DocumentResponseDto toDto(Document document);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntityFromDto(DocumentUpdateDto dto, @MappingTarget Document entity);
}