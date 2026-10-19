package com.dms.rest_api.service;

import com.dms.rest_api.exception.FileStorageException;
import com.dms.rest_api.logging.LogSanitizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.*;
import java.util.Objects;
import java.util.UUID;

/**
 * Service managing physical file operations on the file system.
 */
@Slf4j
@Service
public class FileStorageService {

    private final Path uploadLocation;

    public FileStorageService(@Value("${dms.upload.dir:/app/uploads}") String uploadDir) {
        this.uploadLocation = Paths.get(uploadDir).toAbsolutePath().normalize();
        try {
            Files.createDirectories(this.uploadLocation);
            log.info("Upload directory ready at {}", this.uploadLocation);
        } catch (IOException e) {
            log.error("Could not create upload directory {}", this.uploadLocation, e);
            throw new FileStorageException("Could not create target upload directory on disk.", e);
        }
    }

    /**
     * Stores a file on disk with path traversal protection and unique filename generation.
     */
    public Path store(MultipartFile file) {
        validateFile(file);

        String rawFilename = sanitizeFilename(file.getOriginalFilename());
        String storedFilename = UUID.randomUUID() + "_" + rawFilename;
        Path targetLocation = this.uploadLocation.resolve(storedFilename);

        try {
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);
            log.debug("Stored file '{}' ({} bytes) at {}",
                    LogSanitizer.sanitize(rawFilename), file.getSize(), LogSanitizer.sanitize(targetLocation.toString()));
            return targetLocation;
        } catch (IOException e) {
            log.error("Failed to write file '{}' to {}",
                    LogSanitizer.sanitize(rawFilename), LogSanitizer.sanitize(targetLocation.toString()), e);
            throw new FileStorageException("Failed to store file " + rawFilename, e);
        }
    }

    /**
     * Loads a physical file as a readable Spring Resource.
     */
    public Resource loadAsResource(String storagePath) {
        try {
            Path filePath = Paths.get(storagePath).normalize();
            Resource resource = new UrlResource(filePath.toUri());

            if (resource.exists() || resource.isReadable()) {
                return resource;
            } else {
                log.error("Stored file is missing or unreadable: {}", LogSanitizer.sanitize(storagePath));
                throw new FileStorageException("Could not read file at path: " + storagePath);
            }
        } catch (MalformedURLException e) {
            log.error("Invalid storage path: {}", LogSanitizer.sanitize(storagePath), e);
            throw new FileStorageException("File path URL error: " + storagePath, e);
        }
    }

    /**
     * Deletes a file safely without throwing exception if file does not exist.
     */
    public void deleteQuietly(Path filePath) {
        if (filePath == null) return;
        try {
            if (Files.deleteIfExists(filePath)) {
                log.debug("Deleted file {}", LogSanitizer.sanitize(filePath.toString()));
            }
        } catch (IOException e) {
            // Not rethrown (rollback / redundant deletion), but logged so orphaned files can be found
            log.warn("Could not delete file {}: {}", LogSanitizer.sanitize(filePath.toString()), e.getMessage());
        }
    }

    /**
     * Extracts and cleans the original filename.
     */
    public String sanitizeFilename(String originalFilename) {
        String rawFilename = StringUtils.cleanPath(Objects.requireNonNull(originalFilename));
        if (rawFilename.contains("..")) {
            log.warn("Rejected filename with path traversal sequence: '{}'", LogSanitizer.sanitize(rawFilename));
            throw new FileStorageException("Filename contains invalid path sequence: " + rawFilename);
        }
        return rawFilename;
    }

    private void validateFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            log.warn("Rejected empty upload");
            throw new IllegalArgumentException("Cannot store empty file.");
        }
    }
}