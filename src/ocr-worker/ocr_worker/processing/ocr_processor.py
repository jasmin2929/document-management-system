"""Processing layer: OCR of uploaded documents.

Sprint 3: "empty" worker that only validates the ID and logs.
Sprint 4 will add: load the PDF from MinIO, run Tesseract, send the result on.
"""

import logging

from ocr_worker.exceptions import OcrProcessingException

log = logging.getLogger(__name__)


class OcrProcessor:
    """Runs the OCR for a single document.

    Knows nothing about RabbitMQ: it only receives a document ID, which keeps
    the business logic independent of the messaging layer.
    """

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
        # TODO sprint 4: fetch PDF from MinIO, run Tesseract OCR, publish the result
        log.info("OCR processing finished for document ID: %d (no-op in sprint 3)", document_id)
