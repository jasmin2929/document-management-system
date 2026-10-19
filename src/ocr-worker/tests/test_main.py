import unittest
from unittest.mock import MagicMock, patch

from ocr_worker import __main__ as entry
from ocr_worker.exceptions import BrokerConnectionException

ENV = {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret"}


class MainTest(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_invalid_configuration_returns_exit_code_2(self):
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(2, entry.main())

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_normal_run_returns_0_and_closes_connection(self, consumer_cls, _signal):
        consumer = consumer_cls.return_value
        self.assertEqual(0, entry.main())
        consumer.connect.assert_called_once()
        consumer.start.assert_called_once()
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_broker_unreachable_returns_1(self, consumer_cls, _signal):
        consumer = consumer_cls.return_value
        consumer.connect.side_effect = BrokerConnectionException("down")
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(1, entry.main())
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_shutdown_signal_stops_consumer(self, consumer_cls, signal_mock):
        entry.main()
        handler = signal_mock.call_args_list[0].args[1]
        handler(15, None)  # SIGTERM
        consumer_cls.return_value.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
