import unittest
from unittest.mock import MagicMock

from ocr_worker.exceptions import OcrProcessingException, StorageException
from ocr_worker.model import OcrJob
from ocr_worker.processing.ocr_engine import OcrEngine
from ocr_worker.processing.ocr_processor import OcrProcessor
from ocr_worker.storage.object_storage import ObjectStorageClient

PDF = b"%PDF-1.4 hello"
JOB = OcrJob(document_id=7, object_key="documents/a.pdf", bucket="dms-documents")


class OcrProcessorTest(unittest.TestCase):
    def setUp(self):
        self.storage = MagicMock(spec=ObjectStorageClient)
        self.storage.download.return_value = PDF
        self.engine = MagicMock(spec=OcrEngine)
        self.engine.extract_text.return_value = "Hello World"
        self.processor = OcrProcessor(self.storage, self.engine)

    def test_pdf_is_downloaded_and_ocr_result_returned(self):
        text = self.processor.process(JOB)

        self.storage.download.assert_called_once_with("documents/a.pdf", "dms-documents")
        self.engine.extract_text.assert_called_once_with(PDF)
        self.assertEqual("Hello World", text)

    def test_result_is_logged_with_preview(self):
        with self.assertLogs("ocr_worker.processing.ocr_processor", level="INFO") as logs:
            self.processor.process(JOB)
        self.assertTrue(any("document ID: 7, 11 characters" in l and '"Hello World"' in l for l in logs.output))

    def test_long_text_preview_is_shortened_to_one_line(self):
        self.engine.extract_text.return_value = "line\n" * 100
        with self.assertLogs("ocr_worker.processing.ocr_processor", level="INFO") as logs:
            self.processor.process(JOB)
        finished = [l for l in logs.output if "finished" in l][0]
        self.assertNotIn("\n", finished)
        self.assertTrue(finished.endswith('..."'))

    def test_empty_text_logs_warning(self):
        self.engine.extract_text.return_value = ""
        with self.assertLogs("ocr_worker.processing.ocr_processor", level="WARNING") as logs:
            self.assertEqual("", self.processor.process(JOB))
        self.assertTrue(any("no text" in l for l in logs.output))

    def test_zero_id_raises_without_download(self):
        with self.assertRaisesRegex(OcrProcessingException, "Invalid document ID: 0"):
            self.processor.process(OcrJob(document_id=0, object_key="documents/a.pdf"))
        self.storage.download.assert_not_called()

    def test_negative_id_raises(self):
        with self.assertRaises(OcrProcessingException):
            self.processor.process(OcrJob(document_id=-1, object_key="documents/a.pdf"))

    def test_storage_error_is_passed_on_and_ocr_skipped(self):
        self.storage.download.side_effect = StorageException("missing")
        with self.assertRaises(StorageException):
            self.processor.process(JOB)
        self.engine.extract_text.assert_not_called()

    def test_ocr_error_is_passed_on(self):
        self.engine.extract_text.side_effect = OcrProcessingException("Content is not a PDF document")
        with self.assertRaisesRegex(OcrProcessingException, "not a PDF"):
            self.processor.process(JOB)


if __name__ == "__main__":
    unittest.main()
