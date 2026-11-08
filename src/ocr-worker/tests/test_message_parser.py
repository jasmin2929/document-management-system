import unittest

from ocr_worker.exceptions import MessageFormatException
from ocr_worker.messaging.message_parser import parse_ocr_job
from ocr_worker.model import OcrJob

# Exactly what the REST API's OcrMessageDto looks like as JSON
REST_API_MESSAGE = b'{"documentId": 5, "bucket": "dms-documents", "objectKey": "documents/3f2a.pdf"}'


class ParseOcrJobTest(unittest.TestCase):
    def test_message_from_spring_rest_api(self):
        self.assertEqual(
            OcrJob(document_id=5, object_key="documents/3f2a.pdf", bucket="dms-documents"),
            parse_ocr_job(REST_API_MESSAGE),
        )

    def test_bucket_is_optional(self):
        job = parse_ocr_job(b'{"documentId": 7, "objectKey": "documents/a.pdf"}')
        self.assertIsNone(job.bucket)

    def test_null_bucket_is_treated_as_missing(self):
        job = parse_ocr_job(b'{"documentId": 7, "bucket": null, "objectKey": "documents/a.pdf"}')
        self.assertIsNone(job.bucket)

    def test_invalid_json_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "not valid JSON"):
            parse_ocr_job(b"not json")

    def test_invalid_utf8_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_ocr_job(b"\xff\xfe")

    def test_plain_number_from_sprint_3_raises(self):
        # Without the object key the PDF cannot be found in RustFS
        with self.assertRaisesRegex(MessageFormatException, "JSON object"):
            parse_ocr_job(b"5")

    def test_missing_document_id_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "documentId"):
            parse_ocr_job(b'{"objectKey": "documents/a.pdf"}')

    def test_string_document_id_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "must be an integer"):
            parse_ocr_job(b'{"documentId": "5", "objectKey": "documents/a.pdf"}')

    def test_boolean_document_id_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_ocr_job(b'{"documentId": true, "objectKey": "documents/a.pdf"}')

    def test_float_document_id_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_ocr_job(b'{"documentId": 5.5, "objectKey": "documents/a.pdf"}')

    def test_missing_object_key_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "objectKey"):
            parse_ocr_job(b'{"documentId": 5}')

    def test_blank_object_key_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "objectKey"):
            parse_ocr_job(b'{"documentId": 5, "objectKey": "  "}')

    def test_object_key_with_parent_directory_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "invalid path"):
            parse_ocr_job(b'{"documentId": 5, "objectKey": "documents/../secret.pdf"}')

    def test_absolute_object_key_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "invalid path"):
            parse_ocr_job(b'{"documentId": 5, "objectKey": "/etc/passwd"}')

    def test_empty_bucket_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "bucket"):
            parse_ocr_job(b'{"documentId": 5, "bucket": "", "objectKey": "documents/a.pdf"}')


if __name__ == "__main__":
    unittest.main()
