"""RabbitMQ consumer: takes OCR jobs from the OCR queue and sends each result back on the result queue.

Result messages, read by the REST API:
    {"documentId": 5, "status": "PROCESSED", "content": "recognized text"}
    {"documentId": 5, "status": "FAILED", "content": null}
"""

import json
import logging
import time
from typing import Callable, Optional

import pika
from pika.exceptions import AMQPConnectionError

from ocr_worker.config import Settings
from ocr_worker.exceptions import (
    BrokerConnectionException,
    IndexingException,
    MessageFormatException,
    OcrProcessingException,
    StorageException,
)
from ocr_worker.messaging.message_parser import parse_ocr_job
from ocr_worker.model import OcrJob
from ocr_worker.processing.ocr_processor import OcrProcessor

log = logging.getLogger(__name__)


class OcrQueueConsumer:
    """Lifecycle: connect() -> start() (blocks) -> stop() -> close()."""

    def __init__(
        self,
        settings: Settings,
        processor: OcrProcessor,
        connection_factory: Callable[[pika.ConnectionParameters], pika.BlockingConnection] = pika.BlockingConnection,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._processor = processor
        self._connection_factory = connection_factory
        self._sleep = sleep
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None

    def _connection_parameters(self) -> pika.ConnectionParameters:
        credentials = pika.PlainCredentials(self._settings.rabbitmq_user, self._settings.rabbitmq_password)
        return pika.ConnectionParameters(
            host=self._settings.rabbitmq_host,
            port=self._settings.rabbitmq_port,
            credentials=credentials,
            heartbeat=60,
        )

    def connect(self) -> None:
        """Connect, retrying while the broker is still starting up."""
        params = self._connection_parameters()
        attempts = self._settings.connect_retries
        for attempt in range(1, attempts + 1):
            try:
                self._connection = self._connection_factory(params)
                self._channel = self._connection.channel()
                # Arguments must match the REST API's declaration, otherwise RabbitMQ answers PRECONDITION_FAILED.
                self._channel.queue_declare(queue=self._settings.ocr_queue, durable=True)
                self._channel.queue_declare(queue=self._settings.ocr_result_queue, durable=True)
                # OCR is slow: take one job at a time so other workers can pick up the rest.
                self._channel.basic_qos(prefetch_count=1)
                log.info(
                    "Connected to RabbitMQ at %s:%s, listening on queue '%s'",
                    self._settings.rabbitmq_host, self._settings.rabbitmq_port, self._settings.ocr_queue,
                )
                return
            except AMQPConnectionError as ex:
                log.warning("RabbitMQ not reachable (attempt %d/%d): %s", attempt, attempts, ex)
                if attempt < attempts:
                    self._sleep(self._settings.connect_retry_delay)

        raise BrokerConnectionException(
            f"Could not connect to RabbitMQ at {self._settings.rabbitmq_host}:{self._settings.rabbitmq_port} "
            f"after {attempts} attempts"
        )

    def on_message(self, channel, method, properties, body: bytes) -> None:
        """Process one job. Failures are rejected without requeue, so a broken job cannot loop forever."""
        delivery_tag = method.delivery_tag
        job: Optional[OcrJob] = None
        try:
            job = parse_ocr_job(body)
            log.info("Received OCR job for document ID: %d", job.document_id)
            text = self._processor.process(job)
            self._publish_result(channel, job.document_id, "PROCESSED", text)
            # Ack last: a crash before this point leaves the job in the queue.
            channel.basic_ack(delivery_tag=delivery_tag)
            return
        except MessageFormatException as ex:
            log.error("Rejected malformed message: %s", ex)
        except StorageException as ex:
            log.error("Could not fetch document from object storage: %s", ex)
        except OcrProcessingException as ex:
            log.error("OCR processing failed: %s", ex)
        except IndexingException as ex:
            log.error("Indexing in Elasticsearch failed: %s", ex)
        except Exception:  # noqa: BLE001 - the worker must keep running
            log.exception("Unexpected error while handling message %r", body)

        # A malformed message has no document ID to report back.
        if job is not None:
            self._publish_result(channel, job.document_id, "FAILED", None)
        channel.basic_nack(delivery_tag=delivery_tag, requeue=False)

    def _publish_result(self, channel, document_id: int, status: str, content: Optional[str]) -> None:
        body = json.dumps({"documentId": document_id, "status": status, "content": content})
        channel.basic_publish(
            exchange="",
            routing_key=self._settings.ocr_result_queue,
            body=body.encode("utf-8"),
            properties=pika.BasicProperties(
                # Spring's JSON converter only parses messages marked as JSON.
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        log.info("Sent OCR result for document ID: %d (%s) to queue '%s'",
                 document_id, status, self._settings.ocr_result_queue)

    def start(self) -> None:
        """Consume messages until stop() is called."""
        if self._channel is None:
            self.connect()
        self._channel.basic_consume(
            queue=self._settings.ocr_queue,
            on_message_callback=self.on_message,
            auto_ack=False,
        )
        log.info("Waiting for messages. To exit press CTRL+C")
        try:
            self._channel.start_consuming()
        except AMQPConnectionError as ex:
            raise BrokerConnectionException(f"Lost connection to RabbitMQ: {ex!r}") from ex

    def stop(self) -> None:
        """Safe to call from a signal handler: pika is not thread-safe, so the stop runs on its own I/O loop."""
        if self._connection is not None and self._connection.is_open:
            self._connection.add_callback_threadsafe(self._channel.stop_consuming)

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            log.info("RabbitMQ connection closed")
