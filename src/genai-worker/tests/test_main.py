import unittest
from unittest.mock import patch

from genai_worker import __main__ as entry
from genai_worker.exceptions import BrokerConnectionException

ENV = {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret", "GEMINI_API_KEY": "key"}


class MainTest(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_invalid_configuration_returns_2(self):
        with self.assertLogs("genai_worker", level="CRITICAL"):
            self.assertEqual(2, entry.main())

    @patch.dict("os.environ", ENV, clear=True)
    @patch("genai_worker.__main__.GenAiQueueConsumer")
    def test_broker_unreachable_returns_1(self, consumer_cls):
        consumer_cls.return_value.connect.side_effect = BrokerConnectionException("down")
        with self.assertLogs("genai_worker", level="CRITICAL"):
            self.assertEqual(1, entry.main())
        consumer_cls.return_value.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("genai_worker.__main__.GenAiQueueConsumer")
    def test_normal_stop_returns_0(self, consumer_cls):
        self.assertEqual(0, entry.main())
        consumer_cls.return_value.start.assert_called_once()
