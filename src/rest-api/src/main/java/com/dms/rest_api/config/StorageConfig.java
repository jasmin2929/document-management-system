package com.dms.rest_api.config;

import com.dms.rest_api.service.ObjectStorageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.checksums.RequestChecksumCalculation;
import software.amazon.awssdk.core.checksums.ResponseChecksumValidation;
import software.amazon.awssdk.core.exception.SdkException;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;

@Slf4j
@Configuration
@EnableConfigurationProperties(StorageProperties.class)
public class StorageConfig {

    @Bean
    public S3Client s3Client(StorageProperties properties) {
        log.info("Object storage endpoint {}, bucket '{}'", properties.endpoint(), properties.bucket());
        return S3Client.builder()
                .endpointOverride(URI.create(properties.endpoint()))
                .region(Region.of(properties.region()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(properties.accessKey(), properties.secretKey())))
                // RustFS serves buckets as http://rustfs:9000/<bucket>, not as <bucket>.rustfs:9000 (AWS style)
                .forcePathStyle(true)
                // newer AWS checksum defaults are not supported by every S3 server
                .requestChecksumCalculation(RequestChecksumCalculation.WHEN_REQUIRED)
                .responseChecksumValidation(ResponseChecksumValidation.WHEN_REQUIRED)
                .build();
    }

    @Bean
    public ApplicationRunner createBucketOnStartup(ObjectStorageService objectStorageService) {
        return args -> {
            try {
                objectStorageService.ensureBucketExists();
            } catch (SdkException e) {
                log.warn("Object storage not reachable at startup, uploads will fail until it is: {}", e.getMessage());
            }
        };
    }
}
