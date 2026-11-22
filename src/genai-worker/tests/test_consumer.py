import json
import unittest
from unittest.mock import MagicMock, call

from pika.exceptions import AMQPConnectionError, ChannelClosed, ChannelWrongStateError, StreamLostError

from genai_worker.config import Settings
from genai_worker.consumer import GenAiQueueConsumer
from genai_worker.exceptions import BrokerConnectionException, GenAiException

MESSAGE = b'{"documentId": 5, "text": "Hello World"}'


def make_settings(retries=3):
    return Settings(rabbitmq_host="rabbitmq", rabbitmq_port=5672, rabbitmq_user="u", rabbitmq_password="p",
                    gemini_api_key="key", connect_retries=retries, connect_retry_delay=0.0)


class ConnectTest(unittest.TestCase):
    def test_connect_declares_durable_queues(self):
        connection = MagicMock()
        consumer = GenAiQueueConsumer(make_settings(), MagicMock(), MagicMock(return_value=connection), MagicMock())
        consumer.connect()
        channel = connection.channel.return_value
        self.assertEqual([call(queue="genai-queue", durable=True), call(queue="genai-result-queue", durable=True)],
                         channel.queue_declare.call_args_list)
        channel.basic_qos.assert_called_once_with(prefetch_count=1)

    def test_connect_retries_then_gives_up(self):
        factory = MagicMock(side_effect=AMQPConnectionError("down"))
        sleep = MagicMock()
        consumer = GenAiQueueConsumer(make_settings(3), MagicMock(), factory, sleep)
        with self.assertLogs("genai_worker.consumer", level="WARNING"):
            with self.assertRaisesRegex(BrokerConnectionException, "after 3 attempts"):
                consumer.connect()
        self.assertEqual(3, factory.call_count)
        self.assertEqual(2, sleep.call_count)

    def test_start_consumes_and_translates_connection_loss(self):
        connection = MagicMock()
        consumer = GenAiQueueConsumer(make_settings(), MagicMock(), MagicMock(return_value=connection), MagicMock())
        connection.channel.return_value.start_consuming.side_effect = AMQPConnectionError("lost")
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            with self.assertRaises(BrokerConnectionException):
                consumer.start()
        connection.channel.return_value.basic_consume.assert_called_once()

    def test_start_translates_channel_closed_by_broker(self):
        connection = MagicMock()
        consumer = GenAiQueueConsumer(make_settings(), MagicMock(), MagicMock(return_value=connection), MagicMock())
        connection.channel.return_value.start_consuming.side_effect = ChannelClosed(404, "NOT_FOUND")
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            with self.assertRaisesRegex(BrokerConnectionException, "Lost connection"):
                consumer.start()

    def test_close_does_not_raise_when_connection_is_already_broken(self):
        connection = MagicMock(is_open=True)
        connection.close.side_effect = StreamLostError("gone")
        consumer = GenAiQueueConsumer(make_settings(), MagicMock(), MagicMock(return_value=connection), MagicMock())
        consumer.connect()
        with self.assertLogs("genai_worker.consumer", level="WARNING") as logs:
            consumer.close()
        self.assertTrue(any("Could not close RabbitMQ connection" in l for l in logs.output))

    def test_stop_and_close(self):
        connection = MagicMock(is_open=True)
        consumer = GenAiQueueConsumer(make_settings(), MagicMock(), MagicMock(return_value=connection), MagicMock())
        consumer.connect()
        consumer.stop()
        connection.add_callback_threadsafe.assert_called_once()
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            consumer.close()
        connection.close.assert_called_once()


class OnMessageTest(unittest.TestCase):
    def setUp(self):
        self.gemini = MagicMock()
        self.gemini.summarize.return_value = "A summary"
        self.consumer = GenAiQueueConsumer(make_settings(), self.gemini, MagicMock(), MagicMock())
        self.channel = MagicMock()
        self.method = MagicMock(delivery_tag=7)

    def published(self):
        for c in self.channel.basic_publish.call_args_list:
            self.assertEqual("genai-result-queue", c.kwargs["routing_key"])
            self.assertEqual("application/json", c.kwargs["properties"].content_type)
        return [json.loads(c.kwargs["body"]) for c in self.channel.basic_publish.call_args_list]

    def test_success_publishes_summary_and_acks(self):
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.gemini.summarize.assert_called_once_with("Hello World")
        self.assertEqual([{"documentId": 5, "status": "SUMMARIZED", "summary": "A summary"}], self.published())
        self.channel.basic_ack.assert_called_once_with(delivery_tag=7)
        self.channel.basic_nack.assert_not_called()

    def test_gemini_failure_publishes_failed_and_nacks_without_requeue(self):
        self.gemini.summarize.side_effect = GenAiException("quota")
        with self.assertLogs("genai_worker.consumer", level="INFO") as logs:
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual([{"documentId": 5, "status": "FAILED", "summary": None}], self.published())
        self.channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)
        self.assertTrue(any("quota" in l for l in logs.output))

    def test_unexpected_error_publishes_failed(self):
        self.gemini.summarize.side_effect = RuntimeError("boom")
        with self.assertLogs("genai_worker.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual("FAILED", self.published()[0]["status"])
        self.channel.basic_nack.assert_called_once()

    def test_malformed_message_is_rejected_without_result(self):
        with self.assertLogs("genai_worker.consumer", level="ERROR"):
            self.consumer.on_message(self.channel, self.method, None, b"garbage")
        self.gemini.summarize.assert_not_called()
        self.channel.basic_publish.assert_not_called()
        self.channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)

    def test_broker_failure_while_publishing_propagates_without_failed_result(self):
        # a broken channel must not be treated like a GenAI error: no second publish, no nack, worker restarts
        self.channel.basic_publish.side_effect = ChannelWrongStateError("Channel is closed.")
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            with self.assertRaisesRegex(BrokerConnectionException, "Could not publish GenAI result for document ID 5"):
                self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        self.assertEqual(1, self.channel.basic_publish.call_count)
        self.channel.basic_ack.assert_not_called()
        self.channel.basic_nack.assert_not_called()

    def test_broker_failure_while_acking_propagates(self):
        self.channel.basic_ack.side_effect = ChannelWrongStateError("Channel is closed.")
        with self.assertLogs("genai_worker.consumer", level="INFO"):
            with self.assertRaisesRegex(BrokerConnectionException, "Could not acknowledge message 7"):
                self.consumer.on_message(self.channel, self.method, None, MESSAGE)
        # only the SUMMARIZED result, no FAILED afterwards
        self.assertEqual([{"documentId": 5, "status": "SUMMARIZED", "summary": "A summary"}], self.published())

    def test_broker_failure_while_rejecting_propagates(self):
        self.channel.basic_nack.side_effect = ChannelWrongStateError("Channel is closed.")
        with self.assertLogs("genai_worker.consumer", level="ERROR"):
            with self.assertRaisesRegex(BrokerConnectionException, "Could not reject message 7"):
                self.consumer.on_message(self.channel, self.method, None, b"garbage")
