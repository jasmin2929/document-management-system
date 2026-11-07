import unittest
from unittest.mock import MagicMock

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.processing.ocr_engine import OcrEngine
from ocr_worker.processing.ocr_processor import OcrProcessor


class OcrProcessorTest(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock(spec=OcrEngine)
        self.processor = OcrProcessor(self.engine)

    def test_default_engine_is_created_when_none_is_given(self):
        self.assertIsInstance(OcrProcessor()._engine, OcrEngine)

    def test_valid_id_is_processed_and_logged(self):
        with self.assertLogs("ocr_worker.processing.ocr_processor", level="INFO") as logs:
            self.processor.process(7)
        self.assertTrue(any("document ID: 7" in line for line in logs.output))

    def test_zero_id_raises(self):
        with self.assertRaisesRegex(OcrProcessingException, "Invalid document ID: 0"):
            self.processor.process(0)

    def test_negative_id_raises(self):
        with self.assertRaises(OcrProcessingException):
            self.processor.process(-1)


if __name__ == "__main__":
    unittest.main()
