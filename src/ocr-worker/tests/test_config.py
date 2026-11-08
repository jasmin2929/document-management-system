import unittest

from ocr_worker.config import load_settings
from ocr_worker.exceptions import ConfigurationException

BASE_ENV = {
    "RABBITMQ_USER": "user", "RABBITMQ_PASSWORD": "secret",
    "STORAGE_ACCESS_KEY": "storage-user", "STORAGE_SECRET_KEY": "storage-secret",
    "ELASTICSEARCH_PASSWORD": "es-secret",
}


class LoadSettingsTest(unittest.TestCase):
    def test_defaults_are_used_when_only_credentials_are_set(self):
        settings = load_settings(BASE_ENV)
        self.assertEqual("rabbitmq", settings.rabbitmq_host)
        self.assertEqual(5672, settings.rabbitmq_port)
        self.assertEqual("ocr-queue", settings.ocr_queue)
        self.assertEqual("ocr-result-queue", settings.ocr_result_queue)
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
            load_settings({k: v for k, v in BASE_ENV.items() if k != "RABBITMQ_USER"})

    def test_blank_password_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "RABBITMQ_PASSWORD"):
            load_settings(dict(BASE_ENV, RABBITMQ_PASSWORD="  "))

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

    def test_ocr_defaults(self):
        settings = load_settings(BASE_ENV)
        self.assertEqual("deu+eng", settings.ocr_language)
        self.assertEqual(300, settings.ocr_dpi)
        self.assertEqual(50, settings.ocr_max_pages)
        self.assertEqual(120.0, settings.ocr_timeout_seconds)

    def test_ocr_values_from_environment_override_defaults(self):
        env = dict(BASE_ENV, OCR_LANGUAGE="eng", OCR_DPI="150", OCR_MAX_PAGES="3", OCR_TIMEOUT_SECONDS="30")
        settings = load_settings(env)
        self.assertEqual("eng", settings.ocr_language)
        self.assertEqual(150, settings.ocr_dpi)
        self.assertEqual(3, settings.ocr_max_pages)
        self.assertEqual(30.0, settings.ocr_timeout_seconds)

    def test_ocr_language_with_command_characters_raises(self):
        # The value ends up in the tesseract command, so anything but language codes is refused
        with self.assertRaisesRegex(ConfigurationException, "OCR_LANGUAGE"):
            load_settings(dict(BASE_ENV, OCR_LANGUAGE="eng --tessdata-dir /etc"))

    def test_ocr_dpi_below_minimum_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "OCR_DPI must be >= 72"):
            load_settings(dict(BASE_ENV, OCR_DPI="10"))

    def test_storage_defaults(self):
        settings = load_settings(BASE_ENV)
        self.assertEqual("http://rustfs:9000", settings.storage_endpoint)
        self.assertEqual("storage-user", settings.storage_access_key)
        self.assertEqual("storage-secret", settings.storage_secret_key)
        self.assertEqual("dms-documents", settings.storage_bucket)
        self.assertEqual("us-east-1", settings.storage_region)
        self.assertEqual(50 * 1024 * 1024, settings.storage_max_file_size)

    def test_storage_values_from_environment_override_defaults(self):
        env = dict(BASE_ENV, STORAGE_ENDPOINT="http://localhost:9000/", STORAGE_BUCKET="b",
                   STORAGE_REGION="eu-central-1", STORAGE_MAX_FILE_SIZE="1000")
        settings = load_settings(env)
        self.assertEqual("http://localhost:9000", settings.storage_endpoint)  # trailing slash removed
        self.assertEqual("b", settings.storage_bucket)
        self.assertEqual("eu-central-1", settings.storage_region)
        self.assertEqual(1000, settings.storage_max_file_size)

    def test_missing_storage_secret_raises(self):
        env = {k: v for k, v in BASE_ENV.items() if k != "STORAGE_SECRET_KEY"}
        with self.assertRaisesRegex(ConfigurationException, "STORAGE_SECRET_KEY"):
            load_settings(env)

    def test_invalid_storage_endpoint_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "STORAGE_ENDPOINT"):
            load_settings(dict(BASE_ENV, STORAGE_ENDPOINT="rustfs:9000"))

    def test_elasticsearch_defaults(self):
        settings = load_settings(BASE_ENV)
        self.assertEqual("http://elasticsearch:9200", settings.elasticsearch_url)
        self.assertEqual("elastic", settings.elasticsearch_user)
        self.assertEqual("es-secret", settings.elasticsearch_password)
        self.assertEqual("documents", settings.elasticsearch_index)

    def test_elasticsearch_values_from_environment_override_defaults(self):
        env = dict(BASE_ENV, ELASTICSEARCH_URL="http://localhost:9200/", ELASTICSEARCH_USER="indexer",
                   ELASTICSEARCH_INDEX="docs")
        settings = load_settings(env)
        self.assertEqual("http://localhost:9200", settings.elasticsearch_url)
        self.assertEqual("indexer", settings.elasticsearch_user)
        self.assertEqual("docs", settings.elasticsearch_index)

    def test_missing_elasticsearch_password_raises(self):
        env = {k: v for k, v in BASE_ENV.items() if k != "ELASTICSEARCH_PASSWORD"}
        with self.assertRaisesRegex(ConfigurationException, "ELASTICSEARCH_PASSWORD"):
            load_settings(env)

    def test_invalid_elasticsearch_url_raises(self):
        with self.assertRaisesRegex(ConfigurationException, "ELASTICSEARCH_URL"):
            load_settings(dict(BASE_ENV, ELASTICSEARCH_URL="elasticsearch:9200"))


if __name__ == "__main__":
    unittest.main()
