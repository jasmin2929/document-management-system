"""Messaging layer: parses the messages the REST API puts into the OCR queue.

The REST API (Spring, ``Jackson2JsonMessageConverter``) sends the document ID
as a JSON number, i.e. the body is just ``5``. An object like
``{"documentId": 5}`` is accepted as well, so the message format can be
extended later without breaking the worker.
"""

import json

from ocr_worker.exceptions import MessageFormatException


def parse_document_id(body: bytes) -> int:
    """Extract the document ID from a raw message body.

    Args:
        body: Raw message payload, e.g. ``b"5"`` or ``b'{"documentId": 5}'``.

    Returns:
        The document ID. Its range (e.g. > 0) is checked by the processing layer.

    Raises:
        MessageFormatException: If the body is not valid UTF-8 JSON or does
            not contain an integer document ID.
    """
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise MessageFormatException(f"Message is not valid JSON: {body!r}") from ex

    if isinstance(payload, dict):
        if "documentId" not in payload:
            raise MessageFormatException(f"Message object has no 'documentId': {payload}")
        payload = payload["documentId"]

    # bool is a subclass of int in Python (True == 1), so exclude it explicitly.
    if isinstance(payload, bool) or not isinstance(payload, int):
        raise MessageFormatException(f"Document ID must be an integer, got: {payload!r}")

    return payload
