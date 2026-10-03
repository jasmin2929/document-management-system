package com.dms.rest_api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Allows the Web UI (served from a different origin in local/dev setups)
 * to call this API directly, in addition to the nginx same-origin proxy used in production.
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${dms.cors.allowed-origins:http://localhost,http://localhost:80,http://localhost:5173}")
    private String[] allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOrigins)
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*");
    }
}
