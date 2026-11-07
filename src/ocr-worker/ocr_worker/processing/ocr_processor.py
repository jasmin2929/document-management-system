"""Processing layer: OCR of uploaded documents.

Sprint 3: "empty" worker that only validates the ID and logs.
Sprint 4: the :class:`OcrEngine` (Ghostscript + Tesseract) is available as ``self._engine``;
fetching the PDF from the object storage and calling it is the next step (task 4).
"""

import logging
from typing import Optional

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.processing.ocr_engine import OcrEngine

log = logging.getLogger(__name__)


class OcrProcessor:
    """Runs the OCR for a single document.

    Knows nothing about RabbitMQ: it only receives a document ID, which keeps
    the business logic independent of the messaging layer.
    """

    def __init__(self, engine: Optional[OcrEngine] = None) -> None:
        """Create the processor.

        Args:
            engine: Turns PDF content into text. Injected so tests can pass a mock.
        """
        self._engine = engine if engine is not None else OcrEngine()

    def process(self, document_id: int) -> None:
        """Process the document with the given ID.

        Args:
            document_id: ID of the document in the REST API's database.

        Raises:
            OcrProcessingException: If the document cannot be processed,
                e.g. because the ID is invalid.
        """
        # Database IDs start at 1, so anything else can never be a real document.
        if document_id <= 0:
            raise OcrProcessingException(f"Invalid document ID: {document_id}")

        log.info("Starting OCR processing for document ID: %d", document_id)
        # TODO sprint 4 task 4: download the PDF from RustFS (bucket + objectKey from the message)
        #  and run: text = self._engine.extract_text(pdf_bytes)
        log.info("OCR processing finished for document ID: %d (no-op until task 4)", document_id)
