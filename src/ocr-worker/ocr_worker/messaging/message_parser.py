"""Messaging layer: parses the messages the REST API puts into the OCR queue.

The REST API (Spring, ``Jackson2JsonMessageConverter``) sends a JSON object::

    {"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/3f2a...c1b.pdf"}

``bucket`` is optional (the worker then uses its configured bucket);
``documentId`` and ``objectKey`` are required, because without the key the PDF cannot be found in the object storage.
"""

import json
from typing import Any

from ocr_worker.exceptions import MessageFormatException
from ocr_worker.model import OcrJob


def parse_ocr_job(body: bytes) -> OcrJob:
    """Turn a raw message body into an :class:`OcrJob`.

    Args:
        body: Raw message payload, e.g.
            ``b'{"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/a.pdf"}'``.

    Returns:
        The parsed job. The range of the document ID (e.g. > 0) is checked by the processing layer.

    Raises:
        MessageFormatException: If the body is not a valid JSON object or a field
            is missing or has the wrong type.
    """
    payload = _load_json(body)
    if not isinstance(payload, dict):
        raise MessageFormatException(f"Message must be a JSON object, got: {payload!r}")

    document_id = _parse_document_id_value(payload.get("documentId"))
    object_key = _parse_object_key(payload.get("objectKey"))

    bucket = payload.get("bucket")
    if bucket is not None and (not isinstance(bucket, str) or not bucket.strip()):
        raise MessageFormatException(f"'bucket' must be a non-empty string, got: {bucket!r}")

    return OcrJob(document_id=document_id, object_key=object_key, bucket=bucket.strip() if bucket else None)


def _load_json(body: bytes) -> Any:
    """Decode the body as UTF-8 JSON."""
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise MessageFormatException(f"Message is not valid JSON: {body!r}") from ex


def _parse_document_id_value(value: Any) -> int:
    """Check that the value is an integer document ID."""
    if value is None:
        raise MessageFormatException("Message has no 'documentId'")
    # bool is a subclass of int in Python (True == 1), so exclude it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise MessageFormatException(f"Document ID must be an integer, got: {value!r}")
    return value


def _parse_object_key(value: Any) -> str:
    """Check that the value is a plain, relative object key."""
    if value is None:
        raise MessageFormatException("Message has no 'objectKey'")
    if not isinstance(value, str) or not value.strip():
        raise MessageFormatException(f"'objectKey' must be a non-empty string, got: {value!r}")
    # The REST API only creates keys like "documents/<uuid>.pdf"; refuse anything that
    # tries to leave that structure.
    if value.startswith("/") or ".." in value.split("/"):
        raise MessageFormatException(f"'objectKey' contains an invalid path: {value!r}")
    return value
