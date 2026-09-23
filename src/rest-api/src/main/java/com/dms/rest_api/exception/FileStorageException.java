package com.dms.rest_api.exception;

/**
 * Exception thrown when physical file I/O or storage operations fail.
 * Translates to HTTP 500 INTERNAL SERVER ERROR.
 */
public class FileStorageException extends RuntimeException {

    public FileStorageException(String message) {
        super(message);
    }

    public FileStorageException(String message, Throwable cause) {
        super(message, cause);
    }
}