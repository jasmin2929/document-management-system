import unittest
from unittest.mock import MagicMock, patch

from ocr_worker import __main__ as entry
from ocr_worker.exceptions import BrokerConnectionException, OcrProcessingException, StorageException

ENV = {
    "RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret",
    "STORAGE_ACCESS_KEY": "storage-user", "STORAGE_SECRET_KEY": "storage-secret",
}


# The OCR tool check and the object storage are replaced by mocks, so these tests
# need neither Ghostscript/Tesseract nor a running RustFS.
@patch("ocr_worker.__main__.create_s3_client")
@patch("ocr_worker.__main__.ObjectStorageClient")
@patch("ocr_worker.__main__.OcrEngine")
class MainTest(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_invalid_configuration_returns_exit_code_2(self, _engine_cls, _storage_cls, _s3_factory):
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(2, entry.main())

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_missing_ocr_tools_returns_exit_code_3(self, consumer_cls, engine_cls, _storage_cls, _s3_factory):
        engine_cls.return_value.check_tools.side_effect = OcrProcessingException("Tesseract is not installed")
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(3, entry.main())
        consumer_cls.return_value.connect.assert_not_called()

    @patch.dict("os.environ", dict(ENV, OCR_LANGUAGE="eng", OCR_DPI="200"), clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_ocr_engine_is_created_from_settings(self, _consumer_cls, _signal, engine_cls, _storage, _s3):
        entry.main()
        engine_cls.assert_called_once_with(language="eng", dpi=200, max_pages=50, timeout_seconds=120.0)

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_normal_run_returns_0_and_closes_connection(self, consumer_cls, _signal, _engine_cls, _storage, _s3):
        consumer = consumer_cls.return_value
        self.assertEqual(0, entry.main())
        consumer.connect.assert_called_once()
        consumer.start.assert_called_once()
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_broker_unreachable_returns_1(self, consumer_cls, _signal, _engine_cls, _storage_cls, _s3_factory):
        consumer = consumer_cls.return_value
        consumer.connect.side_effect = BrokerConnectionException("down")
        with self.assertLogs("ocr_worker", level="CRITICAL"):
            self.assertEqual(1, entry.main())
        consumer.close.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_storage_not_ready_is_logged_but_not_fatal(self, consumer_cls, _signal, _engine_cls, storage_cls, _s3):
        storage_cls.return_value.check_bucket.side_effect = StorageException("not reachable")
        with self.assertLogs("ocr_worker", level="WARNING") as logs:
            self.assertEqual(0, entry.main())
        self.assertTrue(any("Object storage not ready" in l for l in logs.output))
        consumer_cls.return_value.start.assert_called_once()

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_storage_client_is_created_from_settings(self, _consumer_cls, _signal, _engine_cls, storage_cls, s3):
        entry.main()
        storage_cls.assert_called_once_with(
            s3.return_value, default_bucket="dms-documents", max_file_size=50 * 1024 * 1024
        )

    @patch.dict("os.environ", ENV, clear=True)
    @patch("ocr_worker.__main__.signal.signal")
    @patch("ocr_worker.__main__.OcrQueueConsumer")
    def test_shutdown_signal_stops_consumer(self, consumer_cls, signal_mock, _engine_cls, _storage, _s3):
        entry.main()
        handler = signal_mock.call_args_list[0].args[1]
        handler(15, None)  # SIGTERM
        consumer_cls.return_value.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
