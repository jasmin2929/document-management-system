package com.dms.rest_api.service;

import com.dms.rest_api.exception.SearchException;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Full-text search over the OCR text the OCR worker indexed in Elasticsearch. */
@Service
public class SearchService {

    private static final int MAX_RESULTS = 100;

    private final RestClient elasticsearch;
    private final String index;

    public SearchService(RestClient.Builder builder,
                         @Value("${dms.elasticsearch.url}") String url,
                         @Value("${dms.elasticsearch.username}") String username,
                         @Value("${dms.elasticsearch.password}") String password,
                         @Value("${dms.elasticsearch.index}") String index) {
        this.elasticsearch = builder.baseUrl(url)
                .defaultHeaders(headers -> headers.setBasicAuth(username, password))
                .build();
        this.index = index;
    }

    /** Returns the IDs of the matching documents, best match first. Tolerates typos (fuzzy). */
    public List<Long> searchDocumentIds(String query) {
        Map<String, Object> request = Map.of(
                "query", Map.of("match", Map.of("content", Map.of("query", query, "fuzziness", "AUTO"))),
                "_source", false,
                "size", MAX_RESULTS);
        try {
            JsonNode response = elasticsearch.post()
                    .uri("/{index}/_search?ignore_unavailable=true", index)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(JsonNode.class);
            List<Long> ids = new ArrayList<>();
            response.path("hits").path("hits").forEach(hit -> ids.add(hit.path("_id").asLong()));
            return ids;
        } catch (RestClientException ex) {
            throw new SearchException("Search is currently not available", ex);
        }
    }
}
