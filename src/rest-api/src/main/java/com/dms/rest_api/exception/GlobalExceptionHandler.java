package com.dms.rest_api.exception;

import com.dms.rest_api.logging.LogSanitizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.TypeMismatchException;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** Shown to the client for unexpected errors; the details only go to the server log. */
    static final String GENERIC_ERROR_MESSAGE = "An unexpected error occurred. Please try again later.";

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleResourceNotFound(ResourceNotFoundException ex) {
        log.warn("Resource not found: {}", LogSanitizer.sanitize(ex.getMessage()));
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", HttpStatus.NOT_FOUND.value());
        body.put("error", "Not Found");
        body.put("message", ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    @ExceptionHandler(FileStorageException.class)
    public ResponseEntity<Map<String, Object>> handleFileStorage(FileStorageException ex) {
        // Server-side fault: log the full stack trace so the root cause can be investigated
        log.error("File storage error: {}", LogSanitizer.sanitize(ex.getMessage()), ex);
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", HttpStatus.INTERNAL_SERVER_ERROR.value());
        body.put("error", "Storage Error");
        body.put("message", ex.getMessage());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgument(IllegalArgumentException ex) {
        log.warn("Bad request: {}", LogSanitizer.sanitize(ex.getMessage()));
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", HttpStatus.BAD_REQUEST.value());
        body.put("error", "Bad Request");
        body.put("message", ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrityViolation(DataIntegrityViolationException ex) {
        // The client only gets a generic message; the database detail is kept in the server log
        log.warn("Database constraint violated: {}", LogSanitizer.sanitize(ex.getMostSpecificCause().getMessage()));
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", HttpStatus.CONFLICT.value());
        body.put("error", "Conflict");
        body.put("message", "The request was not completed because the value you entered already exists.");
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, Object> body = new HashMap<>();
        Map<String, String> errors = new HashMap<>();

        ex.getBindingResult().getFieldErrors().forEach(error -> 
            errors.put(error.getField(), error.getDefaultMessage())
        );

        log.warn("Validation failed for fields {}", errors.keySet());

        body.put("timestamp", LocalDateTime.now());
        body.put("status", HttpStatus.BAD_REQUEST.value());
        body.put("error", "Validation Failed");
        body.put("errors", errors);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(SearchException.class)
    public ResponseEntity<Map<String, Object>> handleSearch(SearchException ex) {
        // The cause may be null; calling getCause().getMessage() blindly would throw inside the handler
        String reason = ex.getCause() != null ? ex.getCause().getMessage() : ex.getMessage();
        log.error("Search failed: {}", LogSanitizer.sanitize(reason));
        return buildResponse(HttpStatus.SERVICE_UNAVAILABLE, "Search Unavailable", ex.getMessage());
    }

    @ExceptionHandler(MessagingException.class)
    public ResponseEntity<Map<String, Object>> handleMessaging(MessagingException ex) {
        // 503 instead of 500: the broker is temporarily unavailable, the client may retry later.
        // The stack trace is already logged where the exception is thrown (DocumentService).
        log.error("Message broker unavailable: {}", LogSanitizer.sanitize(ex.getMessage()));
        return buildResponse(HttpStatus.SERVICE_UNAVAILABLE, "Messaging Error", ex.getMessage());
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleMaxUploadSize(MaxUploadSizeExceededException ex) {
        long maxBytes = ex.getMaxUploadSize();
        String message = maxBytes > 0
                ? "The file exceeds the maximum upload size of " + (maxBytes / (1024 * 1024)) + " MB."
                : "The file exceeds the maximum upload size.";
        log.warn("Upload rejected: {}", message);
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "Content Too Large", message);
    }

    /**
     * Malformed JSON, an unknown enum value or a non-numeric path variable (e.g. /api/documents/abc).
     * These are client errors, but they do not implement ErrorResponse, so without this handler the
     * catch-all below would turn them into a 500. Parser details are not echoed to the client.
     */
    @ExceptionHandler({HttpMessageNotReadableException.class, TypeMismatchException.class})
    public ResponseEntity<Map<String, Object>> handleUnreadableInput(Exception ex) {
        log.warn("Rejected unreadable request input: {}", LogSanitizer.sanitize(ex.getMessage()));
        String message;
        if (ex instanceof TypeMismatchException typeMismatch) {
            // only the parameter name (defined by us) is returned, never the value the client sent
            message = typeMismatch.getPropertyName() != null
                    ? "Parameter '" + typeMismatch.getPropertyName() + "' has an invalid value."
                    : "A request parameter has an invalid value.";
        } else {
            message = "The request body is missing or not valid JSON.";
        }
        return buildResponse(HttpStatus.BAD_REQUEST, "Bad Request", message);
    }

    /**
     * Last line of defence: every exception without a dedicated handler ends up here.
     * Spring MVC exceptions (405, 415, missing parameter, ...) implement ErrorResponse and keep their own
     * status code; everything else becomes a generic 500 so no internal details leak to the client.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleUnexpected(Exception ex) {
        if (ex instanceof ErrorResponse errorResponse) {
            HttpStatusCode status = errorResponse.getStatusCode();
            String detail = errorResponse.getBody().getDetail();
            if (status.is5xxServerError()) {
                log.error("Request failed with {}: {}", status.value(), LogSanitizer.sanitize(ex.getMessage()), ex);
            } else {
                log.warn("Request rejected with {}: {}", status.value(), LogSanitizer.sanitize(ex.getMessage()));
            }
            return buildResponse(status, reasonPhrase(status), detail != null ? detail : reasonPhrase(status));
        }

        // Unknown server-side fault: full stack trace in the log, generic message for the client
        log.error("Unexpected error: {}", LogSanitizer.sanitize(ex.getMessage()), ex);
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", GENERIC_ERROR_MESSAGE);
    }

    private static ResponseEntity<Map<String, Object>> buildResponse(HttpStatusCode status, String error, String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", status.value());
        body.put("error", error);
        body.put("message", message);
        return ResponseEntity.status(status).body(body);
    }

    private static String reasonPhrase(HttpStatusCode status) {
        HttpStatus known = HttpStatus.resolve(status.value());
        return known != null ? known.getReasonPhrase() : "Error";
    }
}