import json
import unittest
from unittest.mock import MagicMock, call

from pika.exceptions import AMQPConnectionError

from ocr_worker.config import Settings
from ocr_worker.exceptions import (
    BrokerConnectionException,
    IndexingException,
    OcrProcessingException,
    StorageException,
)
from ocr_worker.messaging.consumer import OcrQueueConsumer
from ocr_worker.model import OcrJob

MESSAGE = b'{"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/a.pdf"}'


def make_settings(retries=3):
    return Settings(
        rabbitmq_host="rabbitmq", rabbitmq_port=5672, rabbitmq_user="user",
        rabbitmq_password="secret", ocr_queue="ocr-queue", log_level="INFO",
        connect_retries=retries, connect_retry_delay=0.0,
    )


class ConnectTest(unittest.TestCase):
    def test_connect_declares_durable_queue_and_prefetch(self):
        connection = MagicMock()
        factory = MagicMock(return_value=connection)
        consumer = OcrQueueConsumer(make_settings(), MagicMock(), connection_factory=factory, sleep=MagicMock())

        consumer.connect()

        channel = connection.channel.return_value
        self.assertEqual(
            [call(queue="ocr-queue", durable=True), call(queue="ocr-result-queue", durable=True)],
            channel.queue_declare.call_args_list,
        )
        channel.basic_qos.assert_called_once_with(prefetch_count=1)

    def test_connect_retries_until_broker_is_up(self):
        connection = MagicMock()
        factory = MagicMock(side_effect=[AMQPConnectionError("down"), connection])
        sleep = MagicMock()
        consumer = OcrQueueConsumer(make_settings(), MagicMock(), connection_factory=factory, sleep=sleep)

        consumer.connect()

        self.assertEqual(2, factory.call_count)
        sleep.assert_called_once_with(0.0)

    def test_connect_gives_up_after_max_retries(self):
        factory = MagicMock(side_effect=AMQPConnectionError("down"))
        sleep = MagicMock()
        consumer = OcrQueueConsumer(make_settings(retries=3), MagicMock(), connection_factory=factory, sleep=sleep)

        with self.assertRaisesRegex(BrokerConnectionException, "after 3 attempts"):
            consumer.connect()
        self.assertEqual(3, factory.call_count)
        self.assertEqual(2, sleep.call_count)  # no sleep after the last attempt


class OnMessageTest(unittest.TestCase):
    def published_results(self):
        """The result messages sent to the result queue, decoded from JSON."""
        for c in self.channel.basic_publish.call_args_list:
            self.assertEqual("ocr-result-queue", c.kwargs["routing_key"])
            self.assertEqual("application/json", c.kwargs["properties"].content_type)
        return [json.loads(c.kwargs["body"]) for c in self.channel.basic_publish.call_args_list]

    def test_success_sends_processed_result_with_text(self):
        self.processor.process.return_value = "Hello World"
        self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual([{"documentId": 5, "status": "PROCESSED", "content": "Hello World"}],
                         self.published_results())

    def test_failure_sends_failed_result(self):
        self.processor.process.side_effect = OcrProcessingException("Content is not a PDF document")
        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual([{"documentId": 5, "status": "FAILED", "content": None}], self.published_results())

    def test_unexpected_error_sends_failed_result(self):
        self.processor.process.side_effect = RuntimeError("boom")
        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual("FAILED", self.published_results()[0]["status"])

    def test_malformed_message_sends_no_result(self):
        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, b"garbage")
        self.channel.basic_publish.assert_not_called()

    def setUp(self):
        self.processor = MagicMock()
        self.processor.process.return_value = "text"
        self.consumer = OcrQueueConsumer(make_settings(), self.processor, connection_factory=MagicMock())
        self.channel = MagicMock()
        self.method = MagicMock(delivery_tag=11)

    def test_valid_message_is_processed_and_acked(self):
        with self.assertLogs("ocr_worker.messaging.consumer", level="INFO") as logs:
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)

        self.processor.process.assert_called_once_with(
            OcrJob(document_id=5, object_key="documents/a.pdf", bucket="dms-documents")
        )
        self.channel.basic_ack.assert_called_once_with(delivery_tag=11)
        self.channel.basic_nack.assert_not_called()
        self.assertTrue(any("Received OCR job for document ID: 5" in l for l in logs.output))

    def test_malformed_message_is_rejected_without_requeue(self):
        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, b"garbage")

        self.processor.process.assert_not_called()
        self.channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)
        self.channel.basic_ack.assert_not_called()

    def test_processing_error_is_rejected_without_requeue(self):
        self.processor.process.side_effect = OcrProcessingException("Invalid document ID: -1")

        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR") as logs:
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)

        self.channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)
        self.assertTrue(any("OCR processing failed" in l for l in logs.output))

    def test_storage_error_is_rejected_without_requeue(self):
        self.processor.process.side_effect = StorageException("'dms-documents/documents/a.pdf' does not exist")

        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR") as logs:
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)

        self.channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)
        self.channel.basic_ack.assert_not_called()
        self.assertTrue(any("object storage" in l for l in logs.output))

    def test_indexing_error_is_rejected_without_requeue(self):
        self.processor.process.side_effect = IndexingException("Elasticsearch not reachable")

        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR") as logs:
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)

        self.channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)
        self.channel.basic_ack.assert_not_called()
        self.assertTrue(any("Indexing in Elasticsearch failed" in l for l in logs.output))

    def test_unexpected_error_does_not_crash_the_worker(self):
        self.processor.process.side_effect = RuntimeError("boom")

        with self.assertLogs("ocr_worker.messaging.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)

        self.channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)


class StartStopTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.is_open = True
        self.channel = self.connection.channel.return_value
        self.consumer = OcrQueueConsumer(
            make_settings(), MagicMock(), connection_factory=MagicMock(return_value=self.connection), sleep=MagicMock()
        )

    def test_start_connects_and_consumes_with_manual_ack(self):
        self.consumer.start()

        self.channel.basic_consume.assert_called_once_with(
            queue="ocr-queue", on_message_callback=self.consumer.on_message, auto_ack=False
        )
        self.channel.start_consuming.assert_called_once()

    def test_lost_connection_while_consuming_raises_broker_exception(self):
        self.channel.start_consuming.side_effect = AMQPConnectionError("lost")

        with self.assertRaisesRegex(BrokerConnectionException, "Lost connection"):
            self.consumer.start()

    def test_stop_schedules_stop_consuming_thread_safe(self):
        self.consumer.connect()
        self.consumer.stop()
        self.connection.add_callback_threadsafe.assert_called_once_with(self.channel.stop_consuming)

    def test_stop_and_close_without_connection_do_nothing(self):
        consumer = OcrQueueConsumer(make_settings(), MagicMock(), connection_factory=MagicMock())
        consumer.stop()
        consumer.close()  # must not raise

    def test_close_closes_open_connection(self):
        self.consumer.connect()
        self.consumer.close()
        self.connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
