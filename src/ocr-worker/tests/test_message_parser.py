import unittest

from ocr_worker.exceptions import MessageFormatException
from ocr_worker.messaging.message_parser import parse_document_id


class ParseDocumentIdTest(unittest.TestCase):
    def test_plain_number_from_spring_rest_api(self):
        self.assertEqual(5, parse_document_id(b"5"))

    def test_object_with_document_id(self):
        self.assertEqual(42, parse_document_id(b'{"documentId": 42}'))

    def test_invalid_json_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "not valid JSON"):
            parse_document_id(b"not json")

    def test_invalid_utf8_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_document_id(b"\xff\xfe")

    def test_object_without_document_id_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "documentId"):
            parse_document_id(b'{"id": 1}')

    def test_string_id_raises(self):
        with self.assertRaisesRegex(MessageFormatException, "must be an integer"):
            parse_document_id(b'"5"')

    def test_float_id_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_document_id(b"5.5")

    def test_boolean_id_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_document_id(b"true")

    def test_null_raises(self):
        with self.assertRaises(MessageFormatException):
            parse_document_id(b"null")


if __name__ == "__main__":
    unittest.main()
