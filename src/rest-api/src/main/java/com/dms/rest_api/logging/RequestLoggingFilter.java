package com.dms.rest_api.logging;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Logs one line per HTTP request (method, path, status, duration) and tags every log line
 * written while handling that request with a short request ID, so related entries can be found together.
 */
@Slf4j
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestLoggingFilter extends OncePerRequestFilter {

    public static final String REQUEST_ID_KEY = "requestId";
    public static final String REQUEST_ID_HEADER = "X-Request-Id";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        // Always generated server-side: trusting a client-supplied ID would allow log injection
        String requestId = UUID.randomUUID().toString().substring(0, 8);
        MDC.put(REQUEST_ID_KEY, requestId);
        response.setHeader(REQUEST_ID_HEADER, requestId);

        long start = System.currentTimeMillis();
        int status = HttpServletResponse.SC_INTERNAL_SERVER_ERROR; // reported if an exception escapes the chain
        try {
            chain.doFilter(request, response);
            status = response.getStatus();
        } finally {
            log.info("{} {} -> {} ({} ms)",
                    request.getMethod(),
                    LogSanitizer.sanitize(request.getRequestURI()),
                    status,
                    System.currentTimeMillis() - start);
            MDC.remove(REQUEST_ID_KEY);
        }
    }
}
