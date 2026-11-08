package com.dms.rest_api.logging;

/** Prevents log injection (CWE-117): user input with line breaks could forge log entries. */
public final class LogSanitizer {

    static final int MAX_LENGTH = 200;

    private LogSanitizer() {
    }

    public static String sanitize(String value) {
        if (value == null) {
            return "null";
        }
        String cleaned = value.replaceAll("\\p{Cntrl}", "_");
        return cleaned.length() > MAX_LENGTH ? cleaned.substring(0, MAX_LENGTH) + "...(truncated)" : cleaned;
    }
}
