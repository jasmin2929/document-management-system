"""Configuration layer: reads and validates the settings from environment variables.

All settings are validated once at startup. Invalid or missing values raise a
:class:`ConfigurationException`, so the worker fails fast with a clear message
instead of crashing later with an obscure error.
"""

import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional

from ocr_worker.exceptions import ConfigurationException

# Log levels supported by Python's logging module.
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Settings:
    """Immutable, validated configuration of the OCR worker.

    Attributes:
        rabbitmq_host: Hostname of the RabbitMQ broker (the Docker service name).
        rabbitmq_port: AMQP port of the broker.
        rabbitmq_user: Username for the broker.
        rabbitmq_password: Password for the broker.
        ocr_queue: Name of the queue the REST API publishes document IDs to.
        log_level: Python log level name, e.g. ``"INFO"``.
        connect_retries: How often to try connecting before giving up.
        connect_retry_delay: Seconds to wait between two connection attempts.
        ocr_language: Tesseract language(s), e.g. ``"deu+eng"`` for German and English.
        ocr_dpi: Resolution Ghostscript renders the PDF pages with; 300 is the usual value for OCR.
        ocr_max_pages: Only the first pages are processed, so a huge PDF cannot block the worker.
        ocr_timeout_seconds: Maximum runtime of one Ghostscript or Tesseract call.
        storage_endpoint: URL of the S3-compatible object storage (RustFS), e.g. ``"http://rustfs:9000"``.
        storage_access_key: S3 access key (user name) for RustFS.
        storage_secret_key: S3 secret key (password) for RustFS.
        storage_bucket: Bucket used when a message does not name one (same as the REST API's bucket).
        storage_region: S3 region; RustFS ignores it, but the S3 client requires one.
        storage_max_file_size: Larger PDFs are not downloaded (bytes).
    """

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    ocr_queue: str
    log_level: str
    connect_retries: int
    connect_retry_delay: float
    # Defaults keep existing callers (e.g. tests) working that only pass the RabbitMQ settings.
    ocr_language: str = "deu+eng"
    ocr_dpi: int = 300
    ocr_max_pages: int = 50
    ocr_timeout_seconds: float = 120.0
    storage_endpoint: str = "http://rustfs:9000"
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "dms-documents"
    storage_region: str = "us-east-1"
    storage_max_file_size: int = 50 * 1024 * 1024


def _get_int(env: Mapping[str, str], name: str, default: int, minimum: int) -> int:
    """Read an integer setting.

    Args:
        env: Source of the environment variables.
        name: Name of the environment variable.
        default: Value used if the variable is not set.
        minimum: Smallest allowed value.

    Returns:
        The parsed integer.

    Raises:
        ConfigurationException: If the value is not an integer or below ``minimum``.
    """
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as ex:
        # Chain the original error (`from ex`) to keep the full traceback.
        raise ConfigurationException(f"{name} must be an integer, got '{raw}'") from ex
    if value < minimum:
        raise ConfigurationException(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_float(env: Mapping[str, str], name: str, default: float) -> float:
    """Read a non-negative floating point setting.

    Args:
        env: Source of the environment variables.
        name: Name of the environment variable.
        default: Value used if the variable is not set.

    Returns:
        The parsed number.

    Raises:
        ConfigurationException: If the value is not a number or negative.
    """
    raw = env.get(name, str(default))
    try:
        value = float(raw)
    except ValueError as ex:
        raise ConfigurationException(f"{name} must be a number, got '{raw}'") from ex
    if value < 0:
        raise ConfigurationException(f"{name} must not be negative, got {value}")
    return value


def _get_required(env: Mapping[str, str], name: str) -> str:
    """Read a mandatory string setting that has no sensible default.

    Args:
        env: Source of the environment variables.
        name: Name of the environment variable.

    Returns:
        The value without leading/trailing whitespace.

    Raises:
        ConfigurationException: If the variable is missing or blank.
    """
    # Treat whitespace-only values as missing, e.g. `RABBITMQ_PASSWORD= ` in a .env file.
    value = env.get(name, "").strip()
    if not value:
        raise ConfigurationException(f"Environment variable {name} is required")
    return value


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Build and validate the worker settings.

    Args:
        env: Mapping to read the variables from. Defaults to ``os.environ``;
            tests pass a plain dict instead, so they do not depend on the
            real environment.

    Returns:
        The validated settings.

    Raises:
        ConfigurationException: If any setting is missing or invalid.
    """
    env = os.environ if env is None else env

    # Accept any casing (e.g. "debug") but store the canonical upper-case name.
    log_level = env.get("LOG_LEVEL", "INFO").upper()
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigurationException(
            f"LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}, got '{log_level}'"
        )

    # Defaults match docker-compose.yml; credentials are required on purpose,
    # so no hard-coded password ends up in the code.
    return Settings(
        rabbitmq_host=env.get("RABBITMQ_HOST", "rabbitmq"),
        rabbitmq_port=_get_int(env, "RABBITMQ_PORT", 5672, minimum=1),
        rabbitmq_user=_get_required(env, "RABBITMQ_USER"),
        rabbitmq_password=_get_required(env, "RABBITMQ_PASSWORD"),
        ocr_queue=env.get("OCR_QUEUE", "ocr-queue"),
        log_level=log_level,
        connect_retries=_get_int(env, "RABBITMQ_CONNECT_RETRIES", 10, minimum=1),
        connect_retry_delay=_get_float(env, "RABBITMQ_CONNECT_RETRY_DELAY", 3.0),
        ocr_language=_get_ocr_language(env),
        ocr_dpi=_get_int(env, "OCR_DPI", 300, minimum=72),
        ocr_max_pages=_get_int(env, "OCR_MAX_PAGES", 50, minimum=1),
        ocr_timeout_seconds=_get_float(env, "OCR_TIMEOUT_SECONDS", 120.0),
        storage_endpoint=_get_endpoint(env),
        storage_access_key=_get_required(env, "STORAGE_ACCESS_KEY"),
        storage_secret_key=_get_required(env, "STORAGE_SECRET_KEY"),
        storage_bucket=env.get("STORAGE_BUCKET", "dms-documents").strip() or "dms-documents",
        storage_region=env.get("STORAGE_REGION", "us-east-1").strip() or "us-east-1",
        storage_max_file_size=_get_int(env, "STORAGE_MAX_FILE_SIZE", 50 * 1024 * 1024, minimum=1),
    )


def _get_endpoint(env: Mapping[str, str]) -> str:
    """Read the URL of the object storage.

    Args:
        env: Source of the environment variables.

    Returns:
        The URL without a trailing slash.

    Raises:
        ConfigurationException: If the value is not an http(s) URL.
    """
    value = env.get("STORAGE_ENDPOINT", "http://rustfs:9000").strip().rstrip("/")
    if not re.fullmatch(r"https?://[^\s/]+(:\d+)?", value):
        raise ConfigurationException(f"STORAGE_ENDPOINT must look like 'http://rustfs:9000', got '{value}'")
    return value


def _get_ocr_language(env: Mapping[str, str]) -> str:
    """Read the Tesseract language setting, e.g. ``"deu+eng"``.

    Args:
        env: Source of the environment variables.

    Returns:
        The language codes joined by ``+``.

    Raises:
        ConfigurationException: If the value is not a list of language codes.
    """
    value = env.get("OCR_LANGUAGE", "deu+eng").strip()
    # The value is passed to the tesseract command, so only allow plain language codes.
    if not re.fullmatch(r"[a-z_]{3,10}(\+[a-z_]{3,10})*", value):
        raise ConfigurationException(f"OCR_LANGUAGE must look like 'deu+eng', got '{value}'")
    return value
