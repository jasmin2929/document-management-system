package com.dms.rest_api.exception;

/**
 * Exception thrown when a requested domain resource (e.g. Document, Category) does not exist.
 * Translates to HTTP 404 NOT FOUND.
 */
public class ResourceNotFoundException extends RuntimeException {

    public ResourceNotFoundException(String message) {
        super(message);
    }
}