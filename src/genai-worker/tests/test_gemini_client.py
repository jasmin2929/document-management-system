import http.client
import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock

from genai_worker.exceptions import GenAiException
from genai_worker.gemini_client import GeminiClient


def ok_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    return response


def summary_payload(text="A short summary."):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def http_error(code, message="boom"):
    body = io.BytesIO(json.dumps({"error": {"message": message}}).encode("utf-8"))
    return urllib.error.HTTPError("http://x", code, "reason", {}, body)


class GeminiClientTest(unittest.TestCase):
    def make(self, responses, retries=3, max_chars=1000):
        self.urlopen = MagicMock(side_effect=responses)
        self.sleep = MagicMock()
        return GeminiClient("secret-key", "gemini-3.8-flash", "https://api.test/v1beta", 5.0, retries,
                            max_chars, urlopen=self.urlopen, sleep=self.sleep)

    def test_returns_summary_and_sends_key_as_header_not_in_url(self):
        client = self.make([ok_response(summary_payload("  Summary.  "))])

        self.assertEqual("Summary.", client.summarize("some document text"))

        request = self.urlopen.call_args.args[0]
        self.assertEqual("https://api.test/v1beta/models/gemini-3.8-flash:generateContent", request.full_url)
        self.assertEqual("secret-key", request.get_header("X-goog-api-key"))
        self.assertIn("some document text", json.loads(request.data)["contents"][0]["parts"][0]["text"])

    def test_successful_call_logs_duration_and_attempt_but_not_the_key(self):
        client = self.make([ok_response(summary_payload())])

        with self.assertLogs("genai_worker.gemini_client", level="INFO") as logs:
            client.summarize("confidential document text")

        self.assertTrue(any("Gemini API responded in" in line and "(attempt 1/3)" in line for line in logs.output))
        self.assertFalse(any("secret-key" in line or "confidential" in line for line in logs.output))

    def test_long_text_is_truncated(self):
        client = self.make([ok_response(summary_payload())], max_chars=1000)
        with self.assertLogs("genai_worker.gemini_client", level="WARNING"):
            client.summarize("x" * 5000)
        sent = json.loads(self.urlopen.call_args.args[0].data)["contents"][0]["parts"][0]["text"]
        self.assertEqual(1000, sent.count("x"))

    def test_retries_on_rate_limit_then_succeeds(self):
        client = self.make([http_error(429), ok_response(summary_payload())])
        with self.assertLogs("genai_worker.gemini_client", level="WARNING"):
            self.assertEqual("A short summary.", client.summarize("text"))
        self.assertEqual(2, self.urlopen.call_count)
        self.sleep.assert_called_once_with(2)

    def test_retries_on_network_error_and_gives_up(self):
        client = self.make([urllib.error.URLError("down")] * 3)
        with self.assertLogs("genai_worker.gemini_client", level="WARNING"):
            with self.assertRaisesRegex(GenAiException, "after 3 attempts"):
                client.summarize("text")
        self.assertEqual(2, self.sleep.call_count)

    def test_retries_when_connection_breaks_while_reading_the_response(self):
        broken = MagicMock()
        broken.read.side_effect = http.client.IncompleteRead(b"")
        broken.__enter__.return_value = broken
        client = self.make([broken, ok_response(summary_payload())])
        with self.assertLogs("genai_worker.gemini_client", level="WARNING") as logs:
            self.assertEqual("A short summary.", client.summarize("text"))
        self.assertEqual(2, self.urlopen.call_count)
        self.assertTrue(any("network error" in l for l in logs.output))

    def test_timeout_is_retried(self):
        client = self.make([TimeoutError("timed out"), ok_response(summary_payload())])
        with self.assertLogs("genai_worker.gemini_client", level="WARNING"):
            self.assertEqual("A short summary.", client.summarize("text"))

    def test_server_error_is_retried_and_reported_after_last_attempt(self):
        client = self.make([http_error(503, "overloaded") for _ in range(3)])
        with self.assertLogs("genai_worker.gemini_client", level="WARNING"):
            with self.assertRaisesRegex(GenAiException, "after 3 attempts \\(HTTP 503: overloaded\\)"):
                client.summarize("text")

    def test_client_error_is_not_retried(self):
        client = self.make([http_error(400, "API key not valid")])
        with self.assertRaisesRegex(GenAiException, "HTTP 400: API key not valid"):
            client.summarize("text")
        self.assertEqual(1, self.urlopen.call_count)

    def test_invalid_json_response(self):
        response = MagicMock()
        response.read.return_value = b"<html>"
        response.__enter__.return_value = response
        with self.assertRaisesRegex(GenAiException, "invalid JSON"):
            self.make([response]).summarize("text")

    def test_blocked_prompt_has_no_summary(self):
        client = self.make([ok_response({"promptFeedback": {"blockReason": "SAFETY"}})])
        with self.assertRaisesRegex(GenAiException, "blocked: SAFETY"):
            client.summarize("text")

    def test_empty_summary_is_an_error(self):
        client = self.make([ok_response(summary_payload("   "))])
        with self.assertRaisesRegex(GenAiException, "empty summary"):
            client.summarize("text")
