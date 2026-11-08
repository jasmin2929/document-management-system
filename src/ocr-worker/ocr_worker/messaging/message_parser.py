"""Parses OCR queue messages: {"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/<uuid>.pdf"}.

bucket is optional (falls back to the configured bucket); documentId and objectKey are required.
"""

import json
from typing import Any

from ocr_worker.exceptions import MessageFormatException
from ocr_worker.model import OcrJob


def parse_ocr_job(body: bytes) -> OcrJob:
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
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise MessageFormatException(f"Message is not valid JSON: {body!r}") from ex


def _parse_document_id_value(value: Any) -> int:
    if value is None:
        raise MessageFormatException("Message has no 'documentId'")
    # bool is a subclass of int (True == 1)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MessageFormatException(f"Document ID must be an integer, got: {value!r}")
    return value


def _parse_object_key(value: Any) -> str:
    if value is None:
        raise MessageFormatException("Message has no 'objectKey'")
    if not isinstance(value, str) or not value.strip():
        raise MessageFormatException(f"'objectKey' must be a non-empty string, got: {value!r}")
    # The REST API only creates "documents/<uuid>.<ext>"; refuse absolute paths and "..".
    if value.startswith("/") or ".." in value.split("/"):
        raise MessageFormatException(f"'objectKey' contains an invalid path: {value!r}")
    return value
