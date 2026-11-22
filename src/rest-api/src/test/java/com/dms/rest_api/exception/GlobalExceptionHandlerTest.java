package com.dms.rest_api.exception;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.mock.http.MockHttpInputMessage;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/** Plain unit tests: the handler has no dependencies, so no Spring context is needed. */
class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    @DisplayName("unexpected exceptions become a generic 500 without internal details")
    void unexpectedException_HidesInternalMessage() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleUnexpected(new NullPointerException("secret.internal.Field is null"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        assertThat(response.getBody())
                .containsEntry("status", 500)
                .containsEntry("message", GlobalExceptionHandler.GENERIC_ERROR_MESSAGE)
                .containsKey("timestamp");
        assertThat(response.getBody().values()).noneMatch(v -> String.valueOf(v).contains("secret"));
    }

    @Test
    @DisplayName("Spring web exceptions keep their own status code (e.g. 405)")
    void springErrorResponse_KeepsStatus() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleUnexpected(new HttpRequestMethodNotSupportedException("PATCH"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.METHOD_NOT_ALLOWED);
        assertThat(response.getBody()).containsEntry("status", 405).containsEntry("error", "Method Not Allowed");
    }

    @Test
    @DisplayName("broker failures are reported as 503 Service Unavailable")
    void messagingException_Returns503() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleMessaging(new MessagingException("Could not dispatch OCR task"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(response.getBody()).containsEntry("message", "Could not dispatch OCR task");
    }

    @Test
    @DisplayName("search failure without a cause does not throw inside the handler")
    void searchExceptionWithoutCause_Returns503() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleSearch(new SearchException("Search is currently unavailable", null));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(response.getBody()).containsEntry("message", "Search is currently unavailable");
    }

    @Test
    @DisplayName("too large uploads are rejected with 413")
    void maxUploadSizeExceeded_Returns413() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleMaxUploadSize(new MaxUploadSizeExceededException(20 * 1024 * 1024));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.PAYLOAD_TOO_LARGE);
        assertThat(response.getBody()).containsEntry("status", 413);
    }

    @Test
    @DisplayName("upload limit unknown (-1) still gives a readable 413 message")
    void maxUploadSizeUnknown_Returns413WithGenericMessage() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleMaxUploadSize(new MaxUploadSizeExceededException(-1));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.PAYLOAD_TOO_LARGE);
        assertThat(response.getBody()).containsEntry("message", "The file exceeds the maximum upload size.");
    }

    @Test
    @DisplayName("malformed JSON becomes 400 without echoing parser details")
    void unreadableJson_Returns400WithoutParserDetails() {
        HttpMessageNotReadableException ex = new HttpMessageNotReadableException(
                "JSON parse error: Unrecognized token 'secretValue'", new MockHttpInputMessage(new byte[0]));

        ResponseEntity<Map<String, Object>> response = handler.handleUnreadableInput(ex);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).containsEntry("message", "The request body is missing or not valid JSON.");
        assertThat(response.getBody().values()).noneMatch(v -> String.valueOf(v).contains("secretValue"));
    }

    @Test
    @DisplayName("search failure keeps the cause out of the client response")
    void searchExceptionWithCause_Returns503() {
        ResponseEntity<Map<String, Object>> response = handler.handleSearch(
                new SearchException("Search is currently not available", new RuntimeException("es:9200 refused")));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(response.getBody().values()).noneMatch(v -> String.valueOf(v).contains("es:9200"));
    }

    @Test
    @DisplayName("not found keeps the client-facing message")
    void resourceNotFound_Returns404() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleResourceNotFound(new ResourceNotFoundException("Document not found with ID: 7"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getBody()).containsEntry("message", "Document not found with ID: 7");
    }
}
