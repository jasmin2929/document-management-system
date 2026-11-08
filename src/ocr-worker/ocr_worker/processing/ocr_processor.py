"""Processing layer: OCR of uploaded documents.

For every job the processor

1. downloads the original PDF from the object storage (RustFS),
2. runs the OCR with the :class:`OcrEngine` (Ghostscript + Tesseract),
3. returns the recognized text (sprint 4 task 6 will hand it to the indexing worker).
"""

import logging

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.model import OcrJob
from ocr_worker.processing.ocr_engine import OcrEngine
from ocr_worker.storage.object_storage import ObjectStorageClient

log = logging.getLogger(__name__)

# Number of characters of the recognized text shown in the log.
_PREVIEW_LENGTH = 200


class OcrProcessor:
    """Runs the OCR for a single document.

    Knows nothing about RabbitMQ: it only receives an :class:`OcrJob`, which keeps
    the business logic independent of the messaging layer.
    """

    def __init__(self, storage: ObjectStorageClient, engine: OcrEngine) -> None:
        """Create the processor.

        Args:
            storage: Downloads the PDF from the object storage. Injected so tests can pass a mock.
            engine: Turns PDF content into text. Injected so tests can pass a mock.
        """
        self._storage = storage
        self._engine = engine

    def process(self, job: OcrJob) -> str:
        """Fetch the document of the job from the object storage and run the OCR on it.

        Args:
            job: Document ID and location of the PDF in the object storage.

        Returns:
            The recognized text (may be empty if the PDF contains no readable text).

        Raises:
            OcrProcessingException: If the ID is invalid or the OCR fails.
            StorageException: If the PDF cannot be downloaded.
        """
        # Database IDs start at 1, so anything else can never be a real document.
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
        return text


def _preview(text: str) -> str:
    """Shorten the text to one log line (no line breaks, at most ``_PREVIEW_LENGTH`` characters)."""
    single_line = " ".join(text.split())
    if len(single_line) <= _PREVIEW_LENGTH:
        return f'"{single_line}"'
    return f'"{single_line[:_PREVIEW_LENGTH]}..."'
