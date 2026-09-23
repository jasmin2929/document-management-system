package com.dms.rest_api.mapper;

import com.dms.rest_api.dto.DocumentResponseDto;
import com.dms.rest_api.dto.DocumentUpdateDto;
import com.dms.rest_api.entity.Category;
import com.dms.rest_api.entity.Document;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThat;

class DocumentMapperTest {

    private final CategoryMapper categoryMapper = Mappers.getMapper(CategoryMapper.class);
    private final DocumentMapper documentMapper = Mappers.getMapper(DocumentMapper.class);

    public DocumentMapperTest() {
        // MapStruct 'uses' Dependency Injection manuell auflösen
        ReflectionTestUtils.setField(documentMapper, "categoryMapper", categoryMapper);
    }

    @Test
    @DisplayName("toDto() maps document entity and nested category")
    void toDto_MapsNestedEntitiesCorrectly() {
        Category category = Category.builder().id(2L).name("Contracts").build();
        Document entity = Document.builder()
                .id(1L)
                .title("NDA.pdf")
                .category(category)
                .build();

        DocumentResponseDto dto = documentMapper.toDto(entity);

        assertThat(dto).isNotNull();
        assertThat(dto.getId()).isEqualTo(1L);
        assertThat(dto.getCategory()).isNotNull();
        assertThat(dto.getCategory().getName()).isEqualTo("Contracts");
    }

    @Test
    @DisplayName("updateEntityFromDto() ignores null properties in DTO (Partial Update)")
    void updateEntityFromDto_IgnoresNullValues() {
        Document existing = Document.builder()
                .id(1L)
                .title("Original Title")
                .originalFileName("original.pdf")
                .build();

        DocumentUpdateDto updateDto = new DocumentUpdateDto();
        updateDto.setTitle("New Title"); // OriginalFileName bleibt null im DTO

        documentMapper.updateEntityFromDto(updateDto, existing);

        assertThat(existing.getTitle()).isEqualTo("New Title");
        assertThat(existing.getOriginalFileName()).isEqualTo("original.pdf"); // Nicht überschrieben
    }
}