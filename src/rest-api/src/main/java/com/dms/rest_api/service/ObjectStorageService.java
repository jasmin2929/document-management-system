package com.dms.rest_api.service;

import com.dms.rest_api.config.StorageProperties;
import com.dms.rest_api.exception.FileStorageException;
import com.dms.rest_api.logging.LogSanitizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.ResponseBytes;
import software.amazon.awssdk.core.exception.SdkException;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.HeadBucketRequest;
import software.amazon.awssdk.services.s3.model.NoSuchBucketException;
import software.amazon.awssdk.services.s3.model.NoSuchKeyException;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.io.InputStream;
import java.util.Locale;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@Service
public class ObjectStorageService {

    static final String KEY_PREFIX = "documents/";

    private final S3Client s3Client;
    private final String bucket;

    public ObjectStorageService(S3Client s3Client, StorageProperties properties) {
        this.s3Client = s3Client;
        this.bucket = properties.bucket();
    }

    public String getBucket() {
        return bucket;
    }

    public void ensureBucketExists() {
        try {
            s3Client.headBucket(HeadBucketRequest.builder().bucket(bucket).build());
            log.info("Bucket '{}' ready", bucket);
        } catch (NoSuchBucketException e) {
            s3Client.createBucket(CreateBucketRequest.builder().bucket(bucket).build());
            log.info("Bucket '{}' created", bucket);
        }
    }

    // Random UUID key: user-controlled file names never end up in the storage path
    public String store(MultipartFile file) {
        validateFile(file);

        String rawFilename = sanitizeFilename(file.getOriginalFilename());
        String objectKey = buildObjectKey(rawFilename);

        PutObjectRequest request = PutObjectRequest.builder()
                .bucket(bucket)
                .key(objectKey)
                .contentType(file.getContentType())
                .contentLength(file.getSize())
                .build();

        try (InputStream content = file.getInputStream()) {
            s3Client.putObject(request, RequestBody.fromInputStream(content, file.getSize()));
            log.debug("Stored file '{}' ({} bytes) as object '{}'",
                    LogSanitizer.sanitize(rawFilename), file.getSize(), objectKey);
            return objectKey;
        } catch (IOException | SdkException e) {
            log.error("Failed to upload file '{}' as object '{}'", LogSanitizer.sanitize(rawFilename), objectKey, e);
            throw new FileStorageException("Failed to store file " + rawFilename, e);
        }
    }

    public Resource load(String objectKey) {
        try {
            ResponseBytes<GetObjectResponse> object = s3Client.getObjectAsBytes(
                    GetObjectRequest.builder().bucket(bucket).key(objectKey).build());
            return new ByteArrayResource(object.asByteArray());
        } catch (NoSuchKeyException e) {
            log.error("Stored object is missing: {}", LogSanitizer.sanitize(objectKey));
            throw new FileStorageException("Could not find stored file: " + objectKey, e);
        } catch (SdkException e) {
            log.error("Failed to download object {}", LogSanitizer.sanitize(objectKey), e);
            throw new FileStorageException("Could not read stored file: " + objectKey, e);
        }
    }

    public void deleteQuietly(String objectKey) {
        if (objectKey == null) return;
        try {
            s3Client.deleteObject(DeleteObjectRequest.builder().bucket(bucket).key(objectKey).build());
            log.debug("Deleted object {}", LogSanitizer.sanitize(objectKey));
        } catch (SdkException e) {
            // Not rethrown (rollback / redundant deletion), but logged so orphaned objects can be found
            log.warn("Could not delete object {}: {}", LogSanitizer.sanitize(objectKey), e.getMessage());
        }
    }

    public String sanitizeFilename(String originalFilename) {
        String rawFilename = StringUtils.cleanPath(Objects.requireNonNull(originalFilename));
        if (rawFilename.contains("..")) {
            log.warn("Rejected filename with path traversal sequence: '{}'", LogSanitizer.sanitize(rawFilename));
            throw new FileStorageException("Filename contains invalid path sequence: " + rawFilename);
        }
        return rawFilename;
    }

    private String buildObjectKey(String filename) {
        String extension = StringUtils.getFilenameExtension(filename);
        // Keep only a plain alphanumeric extension (e.g. "pdf"); anything else is dropped
        String suffix = (extension != null && extension.matches("[A-Za-z0-9]{1,10}"))
                ? "." + extension.toLowerCase(Locale.ROOT)
                : "";
        return KEY_PREFIX + UUID.randomUUID() + suffix;
    }

    private void validateFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            log.warn("Rejected empty upload");
            throw new IllegalArgumentException("Cannot store empty file.");
        }
    }
}
