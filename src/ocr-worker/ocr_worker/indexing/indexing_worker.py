"""Stores the OCR text in Elasticsearch, one entry per document with the document ID as _id.

Indexing a document again (re-upload, redelivered message) overwrites its entry instead of duplicating it.
"""

import logging
from typing import Any

from elasticsearch import ApiError, Elasticsearch, TransportError

from ocr_worker.config import Settings
from ocr_worker.exceptions import IndexingException
from ocr_worker.model import OcrJob

log = logging.getLogger(__name__)


def create_elasticsearch_client(settings: Settings) -> Elasticsearch:
    return Elasticsearch(
        settings.elasticsearch_url,
        basic_auth=(settings.elasticsearch_user, settings.elasticsearch_password),
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )


class IndexingWorker:
    def __init__(self, es_client: Any, index: str) -> None:
        self._es = es_client
        self._index = index

    def check(self) -> str:
        """Return the Elasticsearch version; raises IndexingException if unreachable or login fails."""
        try:
            return self._es.info()["version"]["number"]
        except (ApiError, TransportError) as ex:
            raise IndexingException(f"Elasticsearch not available: {ex}") from ex

    def index(self, job: OcrJob, text: str) -> None:
        document = {"documentId": job.document_id, "objectKey": job.object_key, "content": text}
        try:
            # wait_for: the text is searchable as soon as this call returns
            self._es.index(index=self._index, id=str(job.document_id), document=document, refresh="wait_for")
        except (ApiError, TransportError) as ex:
            raise IndexingException(
                f"Could not index document ID {job.document_id} in '{self._index}': {ex}"
            ) from ex
        log.info("Indexed document ID: %d in Elasticsearch index '%s'", job.document_id, self._index)
