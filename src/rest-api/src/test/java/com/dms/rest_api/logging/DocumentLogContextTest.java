package com.dms.rest_api.logging;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;

import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DocumentLogContextTest {

    @Test
    @DisplayName("run() tags log lines with doc-<id> while the action runs and clears the tag afterwards")
    void run_SetsAndClearsDocumentTag() {
        AtomicReference<String> tagDuringAction = new AtomicReference<>();

        DocumentLogContext.run(8L, () -> tagDuringAction.set(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)));

        assertThat(tagDuringAction.get()).isEqualTo("doc-8");
        assertThat(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)).isNull();
    }

    @Test
    @DisplayName("run() clears the tag even when the action throws")
    void run_Exception_ClearsDocumentTag() {
        assertThatThrownBy(() -> DocumentLogContext.run(8L, () -> {
            throw new IllegalStateException("boom");
        })).isInstanceOf(IllegalStateException.class);

        assertThat(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)).isNull();
    }
}
