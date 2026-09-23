package com.dms.rest_api.dto;

import lombok.Builder;
import lombok.Data;

/**
 * Data Transfer Object representing category data returned to clients.
 */
@Data
@Builder
public class CategoryResponseDto {

    private Long id;
    private String name;
}