package com.dms.rest_api.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Data Transfer Object for category creation requests.
 */
@Data
public class CategoryRequestDto {

    @NotBlank(message = "Category name is required")
    private String name;
}