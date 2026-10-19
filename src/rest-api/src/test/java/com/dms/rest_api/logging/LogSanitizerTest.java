package com.dms.rest_api.logging;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class LogSanitizerTest {

    @Test
    @DisplayName("sanitize() replaces line breaks so a value cannot forge extra log lines")
    void sanitize_LineBreaks_AreReplaced() {
        String forged = "invoice.pdf\r\n2026-10-17 INFO Admin login successful";

        String result = LogSanitizer.sanitize(forged);

        assertThat(result).doesNotContain("\r", "\n");
        assertThat(result).isEqualTo("invoice.pdf__2026-10-17 INFO Admin login successful");
    }

    @Test
    @DisplayName("sanitize() leaves normal values unchanged")
    void sanitize_NormalValue_IsUnchanged() {
        assertThat(LogSanitizer.sanitize("Rechnung März 2026.pdf")).isEqualTo("Rechnung März 2026.pdf");
    }

    @Test
    @DisplayName("sanitize() returns the text 'null' for null values")
    void sanitize_Null_ReturnsNullText() {
        assertThat(LogSanitizer.sanitize(null)).isEqualTo("null");
    }

    @Test
    @DisplayName("sanitize() truncates very long values")
    void sanitize_LongValue_IsTruncated() {
        String result = LogSanitizer.sanitize("a".repeat(LogSanitizer.MAX_LENGTH + 50));

        assertThat(result).startsWith("a".repeat(LogSanitizer.MAX_LENGTH));
        assertThat(result).endsWith("...(truncated)");
    }
}
