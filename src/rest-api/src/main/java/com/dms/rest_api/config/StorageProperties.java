package com.dms.rest_api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "dms.storage")
public record StorageProperties(String endpoint, String accessKey, String secretKey, String bucket, String region) {
}
