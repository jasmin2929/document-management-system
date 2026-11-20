import unittest

from genai_worker.exceptions import MessageFormatException
from genai_worker.message_parser import parse_genai_job


class ParseGenAiJobTest(unittest.TestCase):
    def test_valid_message(self):
        self.assertEqual((5, "Hello"), parse_genai_job(b'{"documentId": 5, "text": "Hello"}'))

    def test_invalid_messages(self):
        for body in [b"garbage", b"\xff", b"[1]", b'{"text": "x"}', b'{"documentId": true, "text": "x"}',
                     b'{"documentId": 0, "text": "x"}', b'{"documentId": "5", "text": "x"}',
                     b'{"documentId": 5}', b'{"documentId": 5, "text": "  "}']:
            with self.subTest(body=body), self.assertRaises(MessageFormatException):
                parse_genai_job(body)
