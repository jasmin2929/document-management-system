package com.dms.rest_api.service;

import com.dms.rest_api.exception.SearchException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class SearchServiceTest {

    private MockRestServiceServer elasticsearch;
    private SearchService searchService;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder();
        elasticsearch = MockRestServiceServer.bindTo(builder).build();
        searchService = new SearchService(builder, "http://es:9200", "elastic", "secret", "documents");
    }

    @Test
    void returnsDocumentIdsInRelevanceOrder() {
        String auth = "Basic " + Base64.getEncoder().encodeToString("elastic:secret".getBytes());
        elasticsearch.expect(requestTo("http://es:9200/documents/_search?ignore_unavailable=true"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header(HttpHeaders.AUTHORIZATION, auth))
                .andExpect(jsonPath("$.query.match.content.query").value("hello"))
                .andExpect(jsonPath("$.query.match.content.fuzziness").value("AUTO"))
                .andRespond(withSuccess("{\"hits\":{\"hits\":[{\"_id\":\"7\"},{\"_id\":\"3\"}]}}",
                        MediaType.APPLICATION_JSON));

        assertThat(searchService.searchDocumentIds("hello")).containsExactly(7L, 3L);
        elasticsearch.verify();
    }

    @Test
    void noHitsReturnsEmptyList() {
        elasticsearch.expect(requestTo("http://es:9200/documents/_search?ignore_unavailable=true"))
                .andRespond(withSuccess("{\"hits\":{\"hits\":[]}}", MediaType.APPLICATION_JSON));

        assertThat(searchService.searchDocumentIds("nothing")).isEmpty();
    }

    @Test
    void elasticsearchErrorThrowsSearchException() {
        elasticsearch.expect(requestTo("http://es:9200/documents/_search?ignore_unavailable=true"))
                .andRespond(withServerError());

        assertThatThrownBy(() -> searchService.searchDocumentIds("hello"))
                .isInstanceOf(SearchException.class);
    }
}
