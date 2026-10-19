import unittest

from ocr_worker.config import load_settings
from ocr_worker.exceptions import ConfigurationException

BASE_ENV = {"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret"}


class LoadSettingsTest(unittest.TestCase):
    def test_defaults_are_used_when_only_credentials_are_set(self):
        settings = load_settings(BASE_ENV)
        self.assertEqual("rabbitmq", settings.rabbitmq_host)
        self.assertEqual(5672, settings.rabbitmq_port)
        self.assertEqual("ocr-queue", settings.ocr_queue)
        self.assertEqual("INFO", settings.log_level)
        self.assertEqual(10, settings.connect_retries)
        self.assertEqual(3.0, settings.connect_retry_delay)

    def test_values_from_environment_override_defaults(self):
        env = dict(BASE_ENV, RABBITMQ_HOST="broker", RABBITMQ_PORT="5673", OCR_QUEUE="q",
                   LOG_LEVEL="debug", RABBITMQ_CONNECT_RETRIES="2", RABBITMQ_CONNECT_RETRY_DELAY="0.5")
        settings = load_settings(env)
        self.assertEqual("broker", settings.rabbitmq_host)
        self.assertEqual(5673, settings.rabbitmq_port)
        self.assertEqual("q", settings.ocr_queue)
        self.assertEqual("DEBUG", settings.log_level)
        self.assertEqual(2, settings.connect_retries)
        self.assertEqual(0.5, settings.connect_retry_delay)

    def test_missing_user_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "RABBITMQ_USER"):
            load_settings({"RABBITMQ_PASSWORD": "secret"})

    def test_blank_password_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "RABBITMQ_PASSWORD"):
            load_settings({"RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "  "})

    def test_non_numeric_port_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "RABBITMQ_PORT must be an integer"):
            load_settings(dict(BASE_ENV, RABBITMQ_PORT="abc"))

    def test_port_below_minimum_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "RABBITMQ_PORT must be >= 1"):
            load_settings(dict(BASE_ENV, RABBITMQ_PORT="0"))

    def test_invalid_retry_delay_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "must be a number"):
            load_settings(dict(BASE_ENV, RABBITMQ_CONNECT_RETRY_DELAY="soon"))

    def test_negative_retry_delay_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "must not be negative"):
            load_settings(dict(BASE_ENV, RABBITMQ_CONNECT_RETRY_DELAY="-1"))

    def test_invalid_log_level_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "LOG_LEVEL"):
            load_settings(dict(BASE_ENV, LOG_LEVEL="LOUD"))


if __name__ == "__main__":
    unittest.main()
