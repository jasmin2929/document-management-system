import json
from typing import Tuple

from genai_worker.exceptions import MessageFormatException


def parse_genai_job(body: bytes) -> Tuple[int, str]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise MessageFormatException(f"Message is not valid JSON: {body[:200]!r}") from ex
    if not isinstance(payload, dict):
        raise MessageFormatException("Message must be a JSON object")

    document_id = payload.get("documentId")
    if isinstance(document_id, bool) or not isinstance(document_id, int) or document_id <= 0:
        raise MessageFormatException(f"'documentId' must be a positive integer, got: {document_id!r}")
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise MessageFormatException(f"'text' must be a non-empty string (document ID {document_id})")
    return document_id, text
