"""Entry point of the OCR worker service.

Run with ``python -m ocr_worker``. Wires the components together (configuration,
logging, processor, queue consumer), registers signal handlers for a graceful
shutdown and translates failures into process exit codes:

* ``0`` - worker stopped normally (e.g. after SIGTERM / CTRL+C)
* ``1`` - RabbitMQ could not be reached or the connection was lost
* ``2`` - invalid configuration (missing or malformed environment variables)

A non-zero exit code lets Docker's restart policy bring the worker back up.
"""

import logging
import signal
import sys

from ocr_worker.config import load_settings
from ocr_worker.exceptions import BrokerConnectionException, ConfigurationException
from ocr_worker.logging_config import configure_logging
from ocr_worker.messaging.consumer import OcrQueueConsumer
from ocr_worker.processing.ocr_processor import OcrProcessor

log = logging.getLogger("ocr_worker")


def main() -> int:
    """Start the OCR worker and block until it is stopped.

    Returns:
        The process exit code (see module docstring).
    """
    # Configure logging with defaults first, so errors while loading the
    # configuration are already logged in the usual format.
    configure_logging()
    try:
        settings = load_settings()
    except ConfigurationException as ex:
        # Retrying makes no sense with a broken configuration: fail fast.
        log.critical("Invalid configuration: %s", ex)
        return 2

    # Re-apply logging with the configured log level.
    configure_logging(settings.log_level)

    # Dependencies are created here and injected via the constructor,
    # which keeps the consumer independent and easy to unit-test.
    consumer = OcrQueueConsumer(settings, OcrProcessor())

    def handle_shutdown(signum, _frame):
        """Stop consuming when the process receives a termination signal."""
        log.info("Received signal %s, shutting down", signal.Signals(signum).name)
        consumer.stop()

    signal.signal(signal.SIGTERM, handle_shutdown)  # sent by `docker compose stop`
    signal.signal(signal.SIGINT, handle_shutdown)   # CTRL+C when run locally

    try:
        consumer.connect()
        consumer.start()  # blocks until stop() is called or the connection is lost
    except BrokerConnectionException as ex:
        log.critical("%s", ex)
        return 1
    finally:
        # Always release the connection, whether the worker stopped normally or failed.
        consumer.close()

    log.info("OCR worker stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
