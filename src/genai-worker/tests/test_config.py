import unittest

from genai_worker.config import load_settings
from genai_worker.exceptions import ConfigurationException

ENV = {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret", "GEMINI_API_KEY": "key"}


class LoadSettingsTest(unittest.TestCase):
    def test_defaults(self):
        s = load_settings(ENV)
        self.assertEqual("genai-queue", s.genai_queue)
        self.assertEqual("genai-result-queue", s.genai_result_queue)
        self.assertEqual("gemini-3.5-flash-lite", s.gemini_model)
        self.assertEqual("key", s.gemini_api_key)

    def test_overrides(self):
        s = load_settings({**ENV, "GEMINI_MODEL": "gemini-2.5-pro", "GEMINI_MAX_RETRIES": "5",
                           "GEMINI_BASE_URL": "http://localhost:1234/"})
        self.assertEqual("gemini-2.5-pro", s.gemini_model)
        self.assertEqual(5, s.gemini_max_retries)
        self.assertEqual("http://localhost:1234", s.gemini_base_url)

    def test_invalid_values(self):
        for name in ["RABBITMQ_USER", "RABBITMQ_PASSWORD", "GEMINI_API_KEY"]:
            with self.subTest(missing=name), self.assertRaises(ConfigurationException):
                load_settings({k: v for k, v in ENV.items() if k != name})
        for bad in [{"GEMINI_API_KEY": "  "}, {"LOG_LEVEL": "LOUD"}, {"GEMINI_MODEL": "a/b?x"},
                    {"GEMINI_BASE_URL": "ftp://x"}, {"GEMINI_MAX_RETRIES": "0"},
                    {"GEMINI_TIMEOUT_SECONDS": "abc"}, {"GEMINI_TIMEOUT_SECONDS": "0"},
                    {"RABBITMQ_PORT": "x"}]:
            with self.subTest(bad=bad), self.assertRaises(ConfigurationException):
                load_settings({**ENV, **bad})
