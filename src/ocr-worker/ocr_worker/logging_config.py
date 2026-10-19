"""Logging setup for the OCR worker.

Logs go to stdout (not to a file), as is common for containers: Docker collects
them and ``docker compose logs`` shows them.
"""

import logging
import sys

# Example: 2026-10-19 15:45:39,129 INFO  [ocr_worker.messaging.consumer] Received ...
LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger.

    Can be called more than once (e.g. first with defaults, then with the
    configured level); ``force=True`` replaces the previous configuration.

    Args:
        level: Log level name, e.g. ``"INFO"`` or ``"DEBUG"``.
    """
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout, force=True)
    # pika logs every connection detail on INFO; keep it quieter
    logging.getLogger("pika").setLevel(logging.WARNING)
