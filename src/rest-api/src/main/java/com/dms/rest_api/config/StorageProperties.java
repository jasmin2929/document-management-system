package com.dms.rest_api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Connection settings for the S3-compatible object storage (RustFS), bound from "dms.storage.*" in application.yaml.
 *
 * @param endpoint  URL of the storage server, e.g. http://rustfs:9000
 * @param accessKey S3 access key (user name)
 * @param secretKey S3 secret key (password)
 * @param bucket    bucket that holds the uploaded documents
 * @param region    S3 region; RustFS ignores it, but the S3 client requires one
 */
@ConfigurationProperties(prefix = "dms.storage")
public record StorageProperties(String endpoint, String accessKey, String secretKey, String bucket, String region) {
}
