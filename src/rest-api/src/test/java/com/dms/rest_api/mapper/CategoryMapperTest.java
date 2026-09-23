package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.CategoryRequestDto;
import com.dms.rest_api.dto.CategoryResponseDto;
import com.dms.rest_api.entity.Category;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;

import static org.assertj.core.api.Assertions.assertThat;

class CategoryMapperTest {

    private final CategoryMapper mapper = Mappers.getMapper(CategoryMapper.class);

    @Test
    @DisplayName("toDto() maps category entity fields to DTO")
    void toDto_MapsFieldsCorrectly() {
        Category entity = Category.builder().id(1L).name("Invoices").build();

        CategoryResponseDto dto = mapper.toDto(entity);

        assertThat(dto).isNotNull();
        assertThat(dto.getId()).isEqualTo(1L);
        assertThat(dto.getName()).isEqualTo("Invoices");
    }

    @Test
    @DisplayName("toEntity() ignores ID and documents collection")
    void toEntity_IgnoresIdAndChildEntities() {
        CategoryRequestDto requestDto = new CategoryRequestDto();
        requestDto.setName("HR");

        Category entity = mapper.toEntity(requestDto);

        assertThat(entity).isNotNull();
        assertThat(entity.getName()).isEqualTo("HR");
        assertThat(entity.getId()).isNull();
        assertThat(entity.getDocuments()).isEmpty();
    }
}