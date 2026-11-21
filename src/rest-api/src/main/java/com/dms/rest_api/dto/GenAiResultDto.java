package com.dms.rest_api.dto;

/** Result from the GenAI worker: {"documentId": 5, "status": "SUMMARIZED", "summary": "..."}; FAILED has no summary. */
public record GenAiResultDto(Long documentId, SummaryStatus status, String summary) {

    public enum SummaryStatus {
        SUMMARIZED,
        FAILED
    }
}
