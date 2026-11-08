package com.dms.rest_api.dto;

import com.dms.rest_api.entity.Document.DocumentStatus;
import lombok.Data;

@Data
public class DocumentUpdateDto {

    private String title;
    private String content;
    private String summary;
    private DocumentStatus status;
    private Long categoryId;
    private Boolean clearCategory;
}