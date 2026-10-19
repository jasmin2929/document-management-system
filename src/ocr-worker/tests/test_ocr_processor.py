import unittest

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.processing.ocr_processor import OcrProcessor


class OcrProcessorTest(unittest.TestCase):
    def setUp(self):
        self.processor = OcrProcessor()

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
