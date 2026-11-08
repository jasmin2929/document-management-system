import unittest
from unittest.mock import MagicMock, patch

from elastic_transport import ApiResponseMeta, ConnectionError as TransportConnectionError, HttpHeaders
from elasticsearch import AuthenticationException

from ocr_worker.config import Settings
from ocr_worker.exceptions import IndexingException
from ocr_worker.indexing.indexing_worker import IndexingWorker, create_elasticsearch_client
from ocr_worker.model import OcrJob

JOB = OcrJob(document_id=7, object_key="documents/a.pdf", bucket="dms-documents")


def api_error(status):
    meta = ApiResponseMeta(status=status, http_version="1.1", headers=HttpHeaders(), duration=0.0, node=None)
    return AuthenticationException("security_exception", meta=meta, body={})


class IndexingWorkerTest(unittest.TestCase):
    def setUp(self):
        self.es = MagicMock()
        self.worker = IndexingWorker(self.es, "documents")

    def test_text_is_indexed_under_the_document_id(self):
        with self.assertLogs("ocr_worker.indexing.indexing_worker", level="INFO") as logs:
            self.worker.index(JOB, "Hello World")

        self.es.index.assert_called_once_with(
            index="documents", id="7",
            document={"documentId": 7, "objectKey": "documents/a.pdf", "content": "Hello World"},
            refresh="wait_for",
        )
        self.assertTrue(any("Indexed document ID: 7" in l for l in logs.output))

    def test_unreachable_elasticsearch_raises_indexing_exception(self):
        self.es.index.side_effect = TransportConnectionError("connection refused")
        with self.assertRaisesRegex(IndexingException, "document ID 7"):
            self.worker.index(JOB, "Hello World")

    def test_rejected_request_raises_indexing_exception(self):
        self.es.index.side_effect = api_error(401)
        with self.assertRaises(IndexingException):
            self.worker.index(JOB, "Hello World")

    def test_check_returns_version(self):
        self.es.info.return_value = {"version": {"number": "9.1.3"}}
        self.assertEqual("9.1.3", self.worker.check())

    def test_check_with_wrong_credentials_raises(self):
        self.es.info.side_effect = api_error(401)
        with self.assertRaisesRegex(IndexingException, "not available"):
            self.worker.check()


class CreateClientTest(unittest.TestCase):
    @patch("ocr_worker.indexing.indexing_worker.Elasticsearch")
    def test_client_uses_url_and_credentials_from_settings(self, es_cls):
        settings = Settings(
            rabbitmq_host="rabbitmq", rabbitmq_port=5672, rabbitmq_user="u", rabbitmq_password="p",
            ocr_queue="ocr-queue", log_level="INFO", connect_retries=1, connect_retry_delay=0.0,
            elasticsearch_url="http://es:9200", elasticsearch_user="elastic", elasticsearch_password="secret",
        )
        create_elasticsearch_client(settings)

        args, kwargs = es_cls.call_args
        self.assertEqual(("http://es:9200",), args)
        self.assertEqual(("elastic", "secret"), kwargs["basic_auth"])


if __name__ == "__main__":
    unittest.main()
