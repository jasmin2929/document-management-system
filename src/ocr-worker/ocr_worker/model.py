"""Data passed between the layers of the OCR worker.

Kept in its own module, so the processing layer does not have to import the
messaging layer (and vice versa).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OcrJob:
    """One OCR task, built from a message of the OCR queue.

    Attributes:
        document_id: ID of the document in the REST API's database.
        object_key: Key of the PDF in the object storage, e.g. ``"documents/3f2a...c1b.pdf"``.
        bucket: Bucket that holds the PDF. ``None`` means "use the configured default bucket".
    """

    document_id: int
    object_key: str
    bucket: Optional[str] = None
