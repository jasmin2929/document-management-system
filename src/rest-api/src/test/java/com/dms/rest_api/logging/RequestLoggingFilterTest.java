package com.dms.rest_api.logging;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.slf4j.MDC;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@ExtendWith(OutputCaptureExtension.class)
class RequestLoggingFilterTest {

    private final RequestLoggingFilter filter = new RequestLoggingFilter();

    @Test
    @DisplayName("Logs method, path and status of every request")
    void doFilter_LogsRequestSummary(CapturedOutput output) throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/documents");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (req, res) -> ((MockHttpServletResponse) res).setStatus(404));

        assertThat(output).contains("GET /api/documents -> 404");
    }

    @Test
    @DisplayName("Request ID is available during the request, returned as header, and cleared afterwards")
    void doFilter_SetsAndClearsRequestId() throws Exception {
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicReference<String> idDuringRequest = new AtomicReference<>();

        filter.doFilter(new MockHttpServletRequest("POST", "/api/documents/upload"), response,
                (req, res) -> idDuringRequest.set(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)));

        assertThat(idDuringRequest.get()).hasSize(8);
        assertThat(response.getHeader(RequestLoggingFilter.REQUEST_ID_HEADER)).isEqualTo(idDuringRequest.get());
        assertThat(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)).isNull();
    }

    @Test
    @DisplayName("Logs status 500 when an exception escapes the filter chain")
    void doFilter_Exception_LogsServerError(CapturedOutput output) {
        FilterChain failingChain = (req, res) -> {
            throw new ServletException("boom");
        };

        assertThatThrownBy(() -> filter.doFilter(
                new MockHttpServletRequest("DELETE", "/api/documents/1"), new MockHttpServletResponse(), failingChain))
                .isInstanceOf(ServletException.class);

        assertThat(output).contains("DELETE /api/documents/1 -> 500");
        assertThat(MDC.get(RequestLoggingFilter.REQUEST_ID_KEY)).isNull();
    }
}
