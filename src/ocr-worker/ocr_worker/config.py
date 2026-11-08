"""Worker settings from environment variables, validated once at startup (fail fast)."""

import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional

from ocr_worker.exceptions import ConfigurationException

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Settings:
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    ocr_queue: str
    log_level: str
    connect_retries: int
    connect_retry_delay: float
    # Defaults let tests build Settings with only the RabbitMQ values.
    ocr_result_queue: str = "ocr-result-queue"
    ocr_language: str = "deu+eng"
    ocr_dpi: int = 300
    ocr_max_pages: int = 50
    ocr_timeout_seconds: float = 120.0
    storage_endpoint: str = "http://rustfs:9000"
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "dms-documents"
    storage_region: str = "us-east-1"  # ignored by RustFS, required by the S3 client
    storage_max_file_size: int = 50 * 1024 * 1024
    elasticsearch_url: str = "http://elasticsearch:9200"
    elasticsearch_user: str = "elastic"
    elasticsearch_password: str = ""
    elasticsearch_index: str = "documents"


def _get_int(env: Mapping[str, str], name: str, default: int, minimum: int) -> int:
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as ex:
        raise ConfigurationException(f"{name} must be an integer, got '{raw}'") from ex
    if value < minimum:
        raise ConfigurationException(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name, str(default))
    try:
        value = float(raw)
    except ValueError as ex:
        raise ConfigurationException(f"{name} must be a number, got '{raw}'") from ex
    if value < 0:
        raise ConfigurationException(f"{name} must not be negative, got {value}")
    return value


def _get_required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigurationException(f"Environment variable {name} is required")
    return value


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    env = os.environ if env is None else env

    log_level = env.get("LOG_LEVEL", "INFO").upper()
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigurationException(
            f"LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}, got '{log_level}'"
        )

    # Credentials have no defaults on purpose: no passwords in the code.
    return Settings(
        rabbitmq_host=env.get("RABBITMQ_HOST", "rabbitmq"),
        rabbitmq_port=_get_int(env, "RABBITMQ_PORT", 5672, minimum=1),
        rabbitmq_user=_get_required(env, "RABBITMQ_USER"),
        rabbitmq_password=_get_required(env, "RABBITMQ_PASSWORD"),
        ocr_queue=env.get("OCR_QUEUE", "ocr-queue"),
        ocr_result_queue=env.get("OCR_RESULT_QUEUE", "ocr-result-queue"),
        log_level=log_level,
        connect_retries=_get_int(env, "RABBITMQ_CONNECT_RETRIES", 10, minimum=1),
        connect_retry_delay=_get_float(env, "RABBITMQ_CONNECT_RETRY_DELAY", 3.0),
        ocr_language=_get_ocr_language(env),
        ocr_dpi=_get_int(env, "OCR_DPI", 300, minimum=72),
        ocr_max_pages=_get_int(env, "OCR_MAX_PAGES", 50, minimum=1),
        ocr_timeout_seconds=_get_float(env, "OCR_TIMEOUT_SECONDS", 120.0),
        storage_endpoint=_get_url(env, "STORAGE_ENDPOINT", "http://rustfs:9000"),
        storage_access_key=_get_required(env, "STORAGE_ACCESS_KEY"),
        storage_secret_key=_get_required(env, "STORAGE_SECRET_KEY"),
        storage_bucket=env.get("STORAGE_BUCKET", "dms-documents").strip() or "dms-documents",
        storage_region=env.get("STORAGE_REGION", "us-east-1").strip() or "us-east-1",
        storage_max_file_size=_get_int(env, "STORAGE_MAX_FILE_SIZE", 50 * 1024 * 1024, minimum=1),
        elasticsearch_url=_get_url(env, "ELASTICSEARCH_URL", "http://elasticsearch:9200"),
        elasticsearch_user=env.get("ELASTICSEARCH_USER", "elastic").strip() or "elastic",
        elasticsearch_password=_get_required(env, "ELASTICSEARCH_PASSWORD"),
        elasticsearch_index=env.get("ELASTICSEARCH_INDEX", "documents").strip() or "documents",
    )


def _get_url(env: Mapping[str, str], name: str, default: str) -> str:
    value = env.get(name, default).strip().rstrip("/")
    if not re.fullmatch(r"https?://[^\s/]+(:\d+)?", value):
        raise ConfigurationException(f"{name} must look like '{default}', got '{value}'")
    return value


def _get_ocr_language(env: Mapping[str, str]) -> str:
    value = env.get("OCR_LANGUAGE", "deu+eng").strip()
    # Passed to the tesseract command, so only plain language codes are allowed.
    if not re.fullmatch(r"[a-z_]{3,10}(\+[a-z_]{3,10})*", value):
        raise ConfigurationException(f"OCR_LANGUAGE must look like 'deu+eng', got '{value}'")
    return value
