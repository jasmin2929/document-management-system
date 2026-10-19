package com.dms.rest_api.exception;

/**
 * Exception thrown when messaging or queue operations (RabbitMQ) fail.
 * Translates to HTTP 500 INTERNAL SERVER ERROR.
 */
public class MessagingException extends RuntimeException {

    public MessagingException(String message) {
        super(message);
    }

    public MessagingException(String message, Throwable cause) {
        super(message, cause);
    }
}