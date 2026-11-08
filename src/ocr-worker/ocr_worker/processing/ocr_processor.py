"""One OCR job: download the PDF from RustFS, run the OCR, index the text in Elasticsearch."""

import logging

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.indexing.indexing_worker import IndexingWorker
from ocr_worker.model import OcrJob
from ocr_worker.processing.ocr_engine import OcrEngine
from ocr_worker.storage.object_storage import ObjectStorageClient

log = logging.getLogger(__name__)

_PREVIEW_LENGTH = 200


class OcrProcessor:
    def __init__(self, storage: ObjectStorageClient, engine: OcrEngine, indexer: IndexingWorker) -> None:
        self._storage = storage
        self._engine = engine
        self._indexer = indexer

    def process(self, job: OcrJob) -> str:
        """Return the recognized text (may be empty)."""
        if job.document_id <= 0:
            raise OcrProcessingException(f"Invalid document ID: {job.document_id}")

        log.info("Starting OCR processing for document ID: %d (object '%s')", job.document_id, job.object_key)

        pdf_content = self._storage.download(job.object_key, job.bucket)
        text = self._engine.extract_text(pdf_content)

        if not text:
            log.warning("OCR found no text in document ID: %d", job.document_id)
        else:
            log.info(
                "OCR processing finished for document ID: %d, %d characters recognized. Preview: %s",
                job.document_id, len(text), _preview(text),
            )
        # Empty texts are indexed too, so every processed document is in the index.
        self._indexer.index(job, text)
        return text


def _preview(text: str) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= _PREVIEW_LENGTH:
        return f'"{single_line}"'
    return f'"{single_line[:_PREVIEW_LENGTH]}..."'
