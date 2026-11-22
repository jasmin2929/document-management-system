import json
import logging
import time
from typing import Callable, Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPError

from genai_worker.config import Settings
from genai_worker.exceptions import BrokerConnectionException, GenAiException, MessageFormatException
from genai_worker.gemini_client import GeminiClient
from genai_worker.message_parser import parse_genai_job

log = logging.getLogger(__name__)


class GenAiQueueConsumer:

    def __init__(
        self,
        settings: Settings,
        gemini: GeminiClient,
        connection_factory: Callable[[pika.ConnectionParameters], pika.BlockingConnection] = pika.BlockingConnection,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._gemini = gemini
        self._connection_factory = connection_factory
        self._sleep = sleep
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None

    def connect(self) -> None:
        s = self._settings
        params = pika.ConnectionParameters(
            host=s.rabbitmq_host, port=s.rabbitmq_port,
            credentials=pika.PlainCredentials(s.rabbitmq_user, s.rabbitmq_password), heartbeat=600,
        )
        for attempt in range(1, s.connect_retries + 1):
            try:
                self._connection = self._connection_factory(params)
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=s.genai_queue, durable=True)
                self._channel.queue_declare(queue=s.genai_result_queue, durable=True)
                self._channel.basic_qos(prefetch_count=1)
                log.info("Connected to RabbitMQ at %s:%s, listening on queue '%s'",
                         s.rabbitmq_host, s.rabbitmq_port, s.genai_queue)
                return
            except AMQPConnectionError as ex:
                log.warning("RabbitMQ not reachable (attempt %d/%d): %s", attempt, s.connect_retries, ex)
                if attempt < s.connect_retries:
                    self._sleep(s.connect_retry_delay)
        raise BrokerConnectionException(
            f"Could not connect to RabbitMQ at {s.rabbitmq_host}:{s.rabbitmq_port} after {s.connect_retries} attempts"
        )

    def on_message(self, channel, method, properties, body: bytes) -> None:
        delivery_tag = method.delivery_tag
        document_id: Optional[int] = None
        try:
            document_id, text = parse_genai_job(body)
            log.info("Received GenAI job for document ID: %d (%d characters)", document_id, len(text))
            summary = self._gemini.summarize(text)
            log.info("Summary created for document ID: %d (%d characters)", document_id, len(summary))
            self._publish_result(channel, document_id, "SUMMARIZED", summary)
            self._ack(channel, delivery_tag)
            return
        except BrokerConnectionException:
            # The broker connection is broken, so neither a FAILED result nor a nack can be delivered.
            # Propagate it: the worker stops, Docker restarts it and the unacked job is redelivered.
            raise
        except MessageFormatException as ex:
            log.error("Rejected malformed message: %s", ex)
        except GenAiException as ex:
            log.error("GenAI summary failed for document ID %s: %s", document_id, ex)
        except Exception:  # noqa: BLE001
            log.exception("Unexpected error while handling message for document ID %s", document_id)

        if document_id is not None:
            self._publish_result(channel, document_id, "FAILED", None)
        self._reject(channel, delivery_tag)

    @staticmethod
    def _ack(channel, delivery_tag: int) -> None:
        try:
            channel.basic_ack(delivery_tag=delivery_tag)
        except AMQPError as ex:
            raise BrokerConnectionException(f"Could not acknowledge message {delivery_tag}: {ex!r}") from ex

    @staticmethod
    def _reject(channel, delivery_tag: int) -> None:
        # requeue=False: a job that failed once would fail again and loop forever
        try:
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
        except AMQPError as ex:
            raise BrokerConnectionException(f"Could not reject message {delivery_tag}: {ex!r}") from ex

    def _publish_result(self, channel, document_id: int, status: str, summary: Optional[str]) -> None:
        body = json.dumps({"documentId": document_id, "status": status, "summary": summary})
        try:
            channel.basic_publish(
                exchange="",
                routing_key=self._settings.genai_result_queue,
                body=body.encode("utf-8"),
                properties=pika.BasicProperties(content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent),
            )
        except AMQPError as ex:
            # pika errors are translated so callers only depend on our own exception types
            raise BrokerConnectionException(
                f"Could not publish GenAI result for document ID {document_id}: {ex!r}"
            ) from ex
        log.info("Sent GenAI result for document ID: %d (%s) to queue '%s'",
                 document_id, status, self._settings.genai_result_queue)

    def start(self) -> None:
        if self._channel is None:
            self.connect()
        self._channel.basic_consume(queue=self._settings.genai_queue, on_message_callback=self.on_message, auto_ack=False)
        log.info("Waiting for messages. To exit press CTRL+C")
        try:
            self._channel.start_consuming()
        except AMQPError as ex:
            # AMQPError also covers a channel closed by the broker (e.g. queue deleted), not only a lost connection
            raise BrokerConnectionException(f"Lost connection to RabbitMQ: {ex!r}") from ex

    def stop(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.add_callback_threadsafe(self._channel.stop_consuming)

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            try:
                self._connection.close()
                log.info("RabbitMQ connection closed")
            except AMQPError as ex:
                # close() runs in a finally block: raising here would hide the original error
                log.warning("Could not close RabbitMQ connection cleanly: %s", ex)
