package com.dms.rest_api.logging;

/**
 * Makes user-controlled values (file names, titles, category names) safe to write into log files.
 * Prevents log injection (CWE-117): a value containing line breaks could otherwise forge fake log entries.
 */
public final class LogSanitizer {

    static final int MAX_LENGTH = 200;

    private LogSanitizer() {
    }

    /**
     * Replaces control characters (e.g. \r, \n, \t) with '_' and truncates overly long values.
     */
    public static String sanitize(String value) {
        if (value == null) {
            return "null";
        }
        String cleaned = value.replaceAll("\\p{Cntrl}", "_");
        return cleaned.length() > MAX_LENGTH ? cleaned.substring(0, MAX_LENGTH) + "...(truncated)" : cleaned;
    }
}
