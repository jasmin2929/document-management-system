package com.dms.rest_api.service;

import com.dms.rest_api.config.StorageProperties;
import com.dms.rest_api.exception.FileStorageException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.io.Resource;
import org.springframework.mock.web.MockMultipartFile;
import software.amazon.awssdk.core.ResponseBytes;
import software.amazon.awssdk.core.exception.SdkClientException;
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

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ObjectStorageServiceTest {

    private static final String BUCKET = "test-bucket";

    @Mock
    private S3Client s3Client;

    private ObjectStorageService objectStorageService;

    @BeforeEach
    void setUp() {
        StorageProperties properties = new StorageProperties("http://localhost:9000", "key", "secret", BUCKET, "us-east-1");
        objectStorageService = new ObjectStorageService(s3Client, properties);
    }

    @Test
    @DisplayName("store() uploads the file content to the bucket under a random object key")
    void store_ValidFile_UploadsObject() throws IOException {
        MockMultipartFile file = new MockMultipartFile("file", "Invoice 2026.PDF", "application/pdf", "Hello World".getBytes());
        ArgumentCaptor<PutObjectRequest> request = ArgumentCaptor.forClass(PutObjectRequest.class);
        ArgumentCaptor<RequestBody> body = ArgumentCaptor.forClass(RequestBody.class);

        String objectKey = objectStorageService.store(file);

        verify(s3Client).putObject(request.capture(), body.capture());
        assertThat(objectKey).matches("documents/[0-9a-f-]{36}\\.pdf");
        assertThat(request.getValue().bucket()).isEqualTo(BUCKET);
        assertThat(request.getValue().key()).isEqualTo(objectKey);
        assertThat(request.getValue().contentType()).isEqualTo("application/pdf");
        assertThat(request.getValue().contentLength()).isEqualTo(11L);
        assertThat(body.getValue().contentStreamProvider().newStream().readAllBytes()).isEqualTo("Hello World".getBytes());
    }

    @Test
    @DisplayName("store() never puts the user-controlled filename into the object key")
    void store_UnusualFilename_KeyContainsOnlyUuid() {
        MockMultipartFile file = new MockMultipartFile("file", "evil name.p%df", "application/pdf", "x".getBytes());

        String objectKey = objectStorageService.store(file);

        assertThat(objectKey).matches("documents/[0-9a-f-]{36}");
    }

    @Test
    @DisplayName("store() throws IllegalArgumentException when file is empty")
    void store_EmptyFile_ThrowsException() {
        MockMultipartFile emptyFile = new MockMultipartFile("file", "empty.txt", "text/plain", new byte[0]);

        assertThatThrownBy(() -> objectStorageService.store(emptyFile))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Cannot store empty file.");
        verifyNoInteractions(s3Client);
    }

    @Test
    @DisplayName("store() wraps storage server errors in a FileStorageException")
    void store_StorageUnavailable_ThrowsFileStorageException() {
        MockMultipartFile file = new MockMultipartFile("file", "test.pdf", "application/pdf", "x".getBytes());
        given(s3Client.putObject(any(PutObjectRequest.class), any(RequestBody.class)))
                .willThrow(SdkClientException.create("Connection refused"));

        assertThatThrownBy(() -> objectStorageService.store(file))
                .isInstanceOf(FileStorageException.class)
                .hasMessageContaining("Failed to store file test.pdf");
    }

    @Test
    @DisplayName("sanitizeFilename() throws FileStorageException on Path Traversal")
    void sanitizeFilename_PathTraversal_ThrowsException() {
        assertThatThrownBy(() -> objectStorageService.sanitizeFilename("../secret.txt"))
                .isInstanceOf(FileStorageException.class)
                .hasMessageContaining("Filename contains invalid path sequence");
    }

    @Test
    @DisplayName("load() returns the object content as a readable resource")
    void load_ExistingObject_ReturnsResource() throws IOException {
        ResponseBytes<GetObjectResponse> bytes = ResponseBytes.fromByteArray(GetObjectResponse.builder().build(), "Content".getBytes());
        given(s3Client.getObjectAsBytes(GetObjectRequest.builder().bucket(BUCKET).key("documents/a.pdf").build()))
                .willReturn(bytes);

        Resource resource = objectStorageService.load("documents/a.pdf");

        assertThat(resource.getContentAsByteArray()).isEqualTo("Content".getBytes());
    }

    @Test
    @DisplayName("load() throws FileStorageException when the object does not exist")
    void load_MissingObject_ThrowsFileStorageException() {
        given(s3Client.getObjectAsBytes(any(GetObjectRequest.class)))
                .willThrow(NoSuchKeyException.builder().message("missing").build());

        assertThatThrownBy(() -> objectStorageService.load("documents/missing.pdf"))
                .isInstanceOf(FileStorageException.class)
                .hasMessageContaining("Could not find stored file");
    }

    @Test
    @DisplayName("deleteQuietly() deletes the object from the bucket")
    void deleteQuietly_ExistingObject_DeletesObject() {
        objectStorageService.deleteQuietly("documents/a.pdf");

        verify(s3Client).deleteObject(DeleteObjectRequest.builder().bucket(BUCKET).key("documents/a.pdf").build());
    }

    @Test
    @DisplayName("deleteQuietly() does not throw when the storage server fails or the key is null")
    void deleteQuietly_FailureOrNull_DoesNotThrow() {
        given(s3Client.deleteObject(any(DeleteObjectRequest.class))).willThrow(SdkClientException.create("down"));

        assertThatCode(() -> objectStorageService.deleteQuietly("documents/a.pdf")).doesNotThrowAnyException();
        assertThatCode(() -> objectStorageService.deleteQuietly(null)).doesNotThrowAnyException();
        verify(s3Client, times(1)).deleteObject(any(DeleteObjectRequest.class));
    }

    @Test
    @DisplayName("ensureBucketExists() creates the bucket when it is missing")
    void ensureBucketExists_MissingBucket_CreatesBucket() {
        given(s3Client.headBucket(any(HeadBucketRequest.class)))
                .willThrow(NoSuchBucketException.builder().message("no bucket").build());

        objectStorageService.ensureBucketExists();

        verify(s3Client).createBucket(CreateBucketRequest.builder().bucket(BUCKET).build());
    }

    @Test
    @DisplayName("ensureBucketExists() does nothing when the bucket already exists")
    void ensureBucketExists_ExistingBucket_DoesNotCreate() {
        objectStorageService.ensureBucketExists();

        verify(s3Client).headBucket(HeadBucketRequest.builder().bucket(BUCKET).build());
        verify(s3Client, never()).createBucket(any(CreateBucketRequest.class));
    }
}
