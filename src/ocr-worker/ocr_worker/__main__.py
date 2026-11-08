"""OCR worker entry point (python -m ocr_worker).

Exit codes (non-zero lets Docker restart the worker):
    0 stopped normally, 1 RabbitMQ unreachable/lost, 2 invalid configuration, 3 OCR tools missing
"""

import logging
import signal
import sys

from ocr_worker.config import load_settings
from ocr_worker.exceptions import (
    BrokerConnectionException,
    ConfigurationException,
    IndexingException,
    OcrProcessingException,
    StorageException,
)
from ocr_worker.indexing.indexing_worker import IndexingWorker, create_elasticsearch_client
from ocr_worker.logging_config import configure_logging
from ocr_worker.messaging.consumer import OcrQueueConsumer
from ocr_worker.processing.ocr_engine import OcrEngine
from ocr_worker.processing.ocr_processor import OcrProcessor
from ocr_worker.storage.object_storage import ObjectStorageClient, create_s3_client

log = logging.getLogger("ocr_worker")


def main() -> int:
    configure_logging()
    try:
        settings = load_settings()
    except ConfigurationException as ex:
        log.critical("Invalid configuration: %s", ex)
        return 2
    configure_logging(settings.log_level)

    engine = OcrEngine(
        language=settings.ocr_language,
        dpi=settings.ocr_dpi,
        max_pages=settings.ocr_max_pages,
        timeout_seconds=settings.ocr_timeout_seconds,
    )
    try:
        log.info("OCR tools ready: %s", engine.check_tools())
    except OcrProcessingException as ex:
        log.critical("OCR tools not available: %s", ex)
        return 3

    # Storage and Elasticsearch checks are not fatal: each job reports its own error.
    storage = ObjectStorageClient(
        create_s3_client(settings),
        default_bucket=settings.storage_bucket,
        max_file_size=settings.storage_max_file_size,
    )
    try:
        storage.check_bucket()
        log.info("Object storage ready: %s, bucket '%s'", settings.storage_endpoint, settings.storage_bucket)
    except StorageException as ex:
        log.warning("Object storage not ready yet, downloads will fail until it is: %s", ex)

    indexer = IndexingWorker(create_elasticsearch_client(settings), settings.elasticsearch_index)
    try:
        log.info("Elasticsearch ready: %s (version %s), index '%s'",
                 settings.elasticsearch_url, indexer.check(), settings.elasticsearch_index)
    except IndexingException as ex:
        log.warning("Elasticsearch not ready yet, indexing will fail until it is: %s", ex)

    consumer = OcrQueueConsumer(settings, OcrProcessor(storage, engine, indexer))

    def handle_shutdown(signum, _frame):
        log.info("Received signal %s, shutting down", signal.Signals(signum).name)
        consumer.stop()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        consumer.connect()
        consumer.start()
    except BrokerConnectionException as ex:
        log.critical("%s", ex)
        return 1
    finally:
        consumer.close()

    log.info("OCR worker stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
