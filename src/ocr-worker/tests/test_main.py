import unittest
from unittest.mock import MagicMock, patch

from ocr_worker import __main__ as entry
from ocr_worker.exceptions import BrokerConnectionException, OcrProcessingException

ENV = {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret"}


# The OCR tool check is replaced by a mock, so these tests do not need Ghostscript/Tesseract installed
@patch("ocr_worker.__main__.OcrEngine")
class MainTest(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_invalid_configuration_returns_exit_code_2(self, _engine_cls):
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(2, entry.main())

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_missing_ocr_tools_returns_exit_code_3(self, consumer_cls, engine_cls):
        engine_cls.return_value.check_tools.side_effect = OcrProcessingException("Tesseract is not installed")
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(3, entry.main())
        consumer_cls.return_value.connect.assert_not_called()

    @patch.dict("os.environ", dict(ENV, OCR_LANGUAGE="eng", OCR_DPI="200"), clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_ocr_engine_is_created_from_settings(self, _consumer_cls, _signal, engine_cls):
        entry.main()
        engine_cls.assert_called_once_with(language="eng", dpi=200, max_pages=50, timeout_seconds=120.0)

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_normal_run_returns_0_and_closes_connection(self, consumer_cls, _signal, _engine_cls):
        consumer = consumer_cls.return_value
        self.assertEqual(0, entry.main())
        consumer.connect.assert_called_once()
        consumer.start.assert_called_once()
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_broker_unreachable_returns_1(self, consumer_cls, _signal, _engine_cls):
        consumer = consumer_cls.return_value
        consumer.connect.side_effect = BrokerConnectionException("down")
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(1, entry.main())
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_shutdown_signal_stops_consumer(self, consumer_cls, signal_mock, _engine_cls):
        entry.main()
        handler = signal_mock.call_args_list[0].args[1]
        handler(15, None)  # SIGTERM
        consumer_cls.return_value.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
