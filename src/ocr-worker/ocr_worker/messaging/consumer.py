"""Messaging layer: RabbitMQ consumer for the OCR queue.

Receives the document IDs that the REST API publishes on upload, hands them to
the :class:`OcrProcessor` and acknowledges or rejects each message depending on
the outcome. Uses pika's ``BlockingConnection`` (one thread, one message at a time).
"""

import logging
import time
from typing import Callable, Optional

import pika
from pika.exceptions import AMQPConnectionError

from ocr_worker.config import Settings
from ocr_worker.exceptions import (
    BrokerConnectionException,
    MessageFormatException,
    OcrProcessingException,
)
from ocr_worker.messaging.message_parser import parse_document_id
from ocr_worker.processing.ocr_processor import OcrProcessor

log = logging.getLogger(__name__)


class OcrQueueConsumer:
    """Consumes document IDs from the OCR queue and delegates them to the processor.

    Typical lifecycle: ``connect()`` -> ``start()`` (blocks) -> ``stop()`` -> ``close()``.
    """

    def __init__(
        self,
        settings: Settings,
        processor: OcrProcessor,
        connection_factory: Callable[[pika.ConnectionParameters], pika.BlockingConnection] = pika.BlockingConnection,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create the consumer. No connection is opened yet.

        Args:
            settings: Validated worker configuration.
            processor: Processing layer that handles each document ID.
            connection_factory: Creates the broker connection. Injected so unit
                tests can pass a mock instead of connecting to a real RabbitMQ.
            sleep: Wait function between connection attempts. Injected so tests
                do not actually wait.
        """
        self._settings = settings
        self._processor = processor
        self._connection_factory = connection_factory
        self._sleep = sleep
        # Set by connect(); None means "not connected yet".
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None

    # ---------- connection ----------

    def _connection_parameters(self) -> pika.ConnectionParameters:
        """Build the pika connection parameters from the settings."""
        credentials = pika.PlainCredentials(self._settings.rabbitmq_user, self._settings.rabbitmq_password)
        return pika.ConnectionParameters(
            host=self._settings.rabbitmq_host,
            port=self._settings.rabbitmq_port,
            credentials=credentials,
            # Heartbeats let both sides detect a dead connection (e.g. broker restart).
            heartbeat=60,
        )

    def connect(self) -> None:
        """Connect to RabbitMQ and prepare the channel.

        Retries while the broker is still starting up (e.g. right after
        ``docker compose up``).

        Raises:
            BrokerConnectionException: If no connection could be established
                after ``settings.connect_retries`` attempts.
        """
        params = self._connection_parameters()
        attempts = self._settings.connect_retries
        for attempt in range(1, attempts + 1):
            try:
                self._connection = self._connection_factory(params)
                self._channel = self._connection.channel()
                # Declaring is idempotent. The arguments must match the REST API's
                # declaration (durable, not exclusive, no auto-delete), otherwise
                # RabbitMQ rejects it with PRECONDITION_FAILED.
                self._channel.queue_declare(queue=self._settings.ocr_queue, durable=True)
                # Fetch only one unacknowledged message at a time: OCR is slow and
                # CPU-heavy, so remaining messages stay available for other workers.
                self._channel.basic_qos(prefetch_count=1)
                log.info(
                    "Connected to RabbitMQ at %s:%s, listening on queue '%s'",
                    self._settings.rabbitmq_host, self._settings.rabbitmq_port, self._settings.ocr_queue,
                )
                return
            except AMQPConnectionError as ex:
                log.warning("RabbitMQ not reachable (attempt %d/%d): %s", attempt, attempts, ex)
                # No pointless wait after the last attempt.
                if attempt < attempts:
                    self._sleep(self._settings.connect_retry_delay)

        # Translate the pika-specific error into this layer's own exception,
        # so callers do not depend on pika.
        raise BrokerConnectionException(
            f"Could not connect to RabbitMQ at {self._settings.rabbitmq_host}:{self._settings.rabbitmq_port} "
            f"after {attempts} attempts"
        )

    # ---------- consuming ----------

    def on_message(self, channel, method, properties, body: bytes) -> None:
        """Handle a single message (pika callback).

        Acknowledges the message on success. On any failure the message is
        rejected *without* requeue: a message that failed once would fail
        again, and requeueing it would create an endless redelivery loop.

        Args:
            channel: Channel the message was received on.
            method: Delivery metadata; provides the ``delivery_tag``.
            properties: AMQP message properties (unused).
            body: Raw message payload, e.g. ``b"5"``.
        """
        delivery_tag = method.delivery_tag
        try:
            document_id = parse_document_id(body)
            log.info("Received document ID for OCR processing: %d", document_id)
            self._processor.process(document_id)
            # Ack only after successful processing, so a crash in between
            # leaves the message in the queue instead of losing it.
            channel.basic_ack(delivery_tag=delivery_tag)
        except MessageFormatException as ex:
            # Messaging layer: the payload itself is broken.
            log.error("Rejected malformed message: %s", ex)
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
        except OcrProcessingException as ex:
            # Processing layer: valid message, but the document cannot be processed.
            log.error("OCR processing failed: %s", ex)
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
        except Exception:  # noqa: BLE001 - last line of defence, the worker must keep running
            # log.exception also logs the stack trace for debugging.
            log.exception("Unexpected error while handling message %r", body)
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)

    def start(self) -> None:
        """Start consuming messages; blocks until ``stop()`` is called.

        Connects first if ``connect()`` has not been called yet.

        Raises:
            BrokerConnectionException: If connecting fails or the connection
                is lost while consuming.
        """
        if self._channel is None:
            self.connect()
        self._channel.basic_consume(
            queue=self._settings.ocr_queue,
            on_message_callback=self.on_message,
            # Manual acknowledgement: on_message decides when a message is done.
            auto_ack=False,
        )
        log.info("Waiting for messages. To exit press CTRL+C")
        try:
            self._channel.start_consuming()
        except AMQPConnectionError as ex:
            # e.g. RabbitMQ was restarted; the container restart policy brings the worker back
            raise BrokerConnectionException(f"Lost connection to RabbitMQ: {ex!r}") from ex

    def stop(self) -> None:
        """Request a clean stop of ``start()``.

        Safe to call from a signal handler or another thread: pika connections
        are not thread-safe, so the stop is scheduled on the connection's own
        I/O loop via ``add_callback_threadsafe``.
        """
        if self._connection is not None and self._connection.is_open:
            self._connection.add_callback_threadsafe(self._channel.stop_consuming)

    def close(self) -> None:
        """Close the broker connection. Does nothing if it is not open."""
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            log.info("RabbitMQ connection closed")
