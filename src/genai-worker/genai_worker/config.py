import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional

from genai_worker.exceptions import ConfigurationException

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Settings:
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    gemini_api_key: str
    log_level: str = "INFO"
    connect_retries: int = 10
    connect_retry_delay: float = 3.0
    genai_queue: str = "genai-queue"
    genai_result_queue: str = "genai-result-queue"
    gemini_model: str = "gemini-3.8-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: float = 60.0
    gemini_max_retries: int = 3
    max_input_chars: int = 200_000


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
    if value <= 0:
        raise ConfigurationException(f"{name} must be positive, got {value}")
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

    model = env.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ConfigurationException(f"GEMINI_MODEL must look like 'gemini-3.8-flash', got '{model}'")

    base_url = env.get("GEMINI_BASE_URL", Settings.gemini_base_url).strip().rstrip("/")
    if not re.fullmatch(r"https?://[^\s]+", base_url):
        raise ConfigurationException(f"GEMINI_BASE_URL must be an http(s) URL, got '{base_url}'")

    return Settings(
        rabbitmq_host=env.get("RABBITMQ_HOST", "rabbitmq"),
        rabbitmq_port=_get_int(env, "RABBITMQ_PORT", 5672, minimum=1),
        rabbitmq_user=_get_required(env, "RABBITMQ_USER"),
        rabbitmq_password=_get_required(env, "RABBITMQ_PASSWORD"),
        gemini_api_key=_get_required(env, "GEMINI_API_KEY"),
        log_level=log_level,
        connect_retries=_get_int(env, "RABBITMQ_CONNECT_RETRIES", 10, minimum=1),
        connect_retry_delay=_get_float(env, "RABBITMQ_CONNECT_RETRY_DELAY", 3.0),
        genai_queue=env.get("GENAI_QUEUE", "genai-queue"),
        genai_result_queue=env.get("GENAI_RESULT_QUEUE", "genai-result-queue"),
        gemini_model=model,
        gemini_base_url=base_url,
        gemini_timeout_seconds=_get_float(env, "GEMINI_TIMEOUT_SECONDS", 60.0),
        gemini_max_retries=_get_int(env, "GEMINI_MAX_RETRIES", 3, minimum=1),
        max_input_chars=_get_int(env, "GENAI_MAX_INPUT_CHARS", 200_000, minimum=1000),
    )
