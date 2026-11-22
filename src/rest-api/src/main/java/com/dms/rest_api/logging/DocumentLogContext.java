package com.dms.rest_api.logging;

import org.slf4j.MDC;

/**
 * Tags log lines written while handling a queue message with "doc-<id>" in the request ID column,
 * so asynchronous results can be traced like HTTP requests, e.g. "INFO [doc-8] ... Summary for document 8 stored".
 */
public final class DocumentLogContext {

    private DocumentLogContext() {
    }

    public static void run(Long documentId, Runnable action) {
        MDC.put(RequestLoggingFilter.REQUEST_ID_KEY, "doc-" + documentId);
        try {
            action.run();
        } finally {
            // listener threads are reused, so the tag must not leak into the next message
            MDC.remove(RequestLoggingFilter.REQUEST_ID_KEY);
        }
    }
}
