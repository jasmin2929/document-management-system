from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OcrJob:
    document_id: int
    object_key: str
    bucket: Optional[str] = None  # None = configured default bucket
