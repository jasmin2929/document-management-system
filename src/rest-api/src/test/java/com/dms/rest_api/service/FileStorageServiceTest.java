package com.dms.rest_api.service;

import com.dms.rest_api.exception.FileStorageException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.core.io.Resource;
import org.springframework.mock.web.MockMultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FileStorageServiceTest {

    private FileStorageService fileStorageService;

    @TempDir
    Path tempUploadDir;

    @BeforeEach
    void setUp() {
        fileStorageService = new FileStorageService(tempUploadDir.toString());
    }

    @Test
    @DisplayName("store() writes binary content correctly to disk")
    void store_ValidFile_SavesFileToDisk() throws IOException {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "hello.txt",
                "text/plain",
                "Hello World".getBytes()
        );

        Path savedPath = fileStorageService.store(file);

        assertThat(Files.exists(savedPath)).isTrue();
        assertThat(Files.readString(savedPath)).isEqualTo("Hello World");
        assertThat(savedPath.getFileName().toString()).endsWith("_hello.txt");
    }

    @Test
    @DisplayName("store() throws IllegalArgumentException when file is empty")
    void store_EmptyFile_ThrowsException() {
        MockMultipartFile emptyFile = new MockMultipartFile("file", "empty.txt", "text/plain", new byte[0]);

        assertThatThrownBy(() -> fileStorageService.store(emptyFile))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Cannot store empty file.");
    }

    @Test
    @DisplayName("sanitizeFilename() cleans path and throws FileStorageException on Path Traversal")
    void sanitizeFilename_PathTraversal_ThrowsException() {
        assertThatThrownBy(() -> fileStorageService.sanitizeFilename("../secret.txt"))
                .isInstanceOf(FileStorageException.class)
                .hasMessageContaining("Filename contains invalid path sequence");
    }

    @Test
    @DisplayName("loadAsResource() successfully returns existing file resource")
    void loadAsResource_ExistingFile_ReturnsReadableResource() throws IOException {
        Path existingFile = tempUploadDir.resolve("sample.txt");
        Files.writeString(existingFile, "Content");

        Resource resource = fileStorageService.loadAsResource(existingFile.toString());

        assertThat(resource.exists()).isTrue();
        assertThat(resource.isReadable()).isTrue();
    }

    @Test
    @DisplayName("deleteQuietly() removes existing file without throwing errors")
    void deleteQuietly_ExistingFile_RemovesFile() throws IOException {
        Path fileToDelete = tempUploadDir.resolve("delete_me.txt");
        Files.writeString(fileToDelete, "Delete");

        fileStorageService.deleteQuietly(fileToDelete);

        assertThat(Files.exists(fileToDelete)).isFalse();
    }
}