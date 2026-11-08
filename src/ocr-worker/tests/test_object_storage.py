import io
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, EndpointConnectionError

from ocr_worker.config import Settings
from ocr_worker.exceptions import StorageException
from ocr_worker.storage.object_storage import ObjectStorageClient, create_s3_client


def client_error(code, operation="GetObject"):
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


def s3_response(content: bytes):
    return {"Body": io.BytesIO(content), "ContentLength": len(content)}


class DownloadTest(unittest.TestCase):
    def setUp(self):
        self.s3 = MagicMock()
        self.storage = ObjectStorageClient(self.s3, default_bucket="dms-documents", max_file_size=100)

    def test_download_returns_object_content(self):
        self.s3.get_object.return_value = s3_response(b"%PDF-1.4")

        self.assertEqual(b"%PDF-1.4", self.storage.download("documents/a.pdf", "other-bucket"))
        self.s3.get_object.assert_called_once_with(Bucket="other-bucket", Key="documents/a.pdf")

    def test_default_bucket_is_used_when_none_given(self):
        self.s3.get_object.return_value = s3_response(b"x")
        self.storage.download("documents/a.pdf")
        self.s3.get_object.assert_called_once_with(Bucket="dms-documents", Key="documents/a.pdf")

    def test_missing_object_raises_storage_exception(self):
        self.s3.get_object.side_effect = client_error("NoSuchKey")
        with self.assertRaisesRegex(StorageException, "does not exist"):
            self.storage.download("documents/missing.pdf")

    def test_missing_bucket_raises_storage_exception(self):
        self.s3.get_object.side_effect = client_error("NoSuchBucket")
        with self.assertRaisesRegex(StorageException, "does not exist"):
            self.storage.download("documents/a.pdf")

    def test_access_denied_raises_storage_exception(self):
        self.s3.get_object.side_effect = client_error("AccessDenied")
        with self.assertRaisesRegex(StorageException, "refused access.*AccessDenied"):
            self.storage.download("documents/a.pdf")

    def test_unreachable_storage_raises_storage_exception(self):
        self.s3.get_object.side_effect = EndpointConnectionError(endpoint_url="http://rustfs:9000")
        with self.assertRaisesRegex(StorageException, "not reachable"):
            self.storage.download("documents/a.pdf")

    def test_too_large_object_is_not_downloaded(self):
        body = MagicMock()
        self.s3.get_object.return_value = {"Body": body, "ContentLength": 101}
        with self.assertRaisesRegex(StorageException, "too large"):
            self.storage.download("documents/big.pdf")
        body.read.assert_not_called()
        body.close.assert_called_once()


class CheckBucketTest(unittest.TestCase):
    def setUp(self):
        self.s3 = MagicMock()
        self.storage = ObjectStorageClient(self.s3, default_bucket="dms-documents", max_file_size=100)

    def test_existing_bucket_passes(self):
        self.storage.check_bucket()
        self.s3.head_bucket.assert_called_once_with(Bucket="dms-documents")

    def test_missing_bucket_raises(self):
        self.s3.head_bucket.side_effect = client_error("404", "HeadBucket")
        with self.assertRaisesRegex(StorageException, "bucket 'dms-documents' does not exist"):
            self.storage.check_bucket()


class CreateS3ClientTest(unittest.TestCase):
    @patch("ocr_worker.storage.object_storage.boto3.client")
    def test_client_uses_endpoint_credentials_and_path_style(self, boto_client):
        settings = Settings(
            rabbitmq_host="rabbitmq", rabbitmq_port=5672, rabbitmq_user="u", rabbitmq_password="p",
            ocr_queue="ocr-queue", log_level="INFO", connect_retries=1, connect_retry_delay=0.0,
            storage_endpoint="http://rustfs:9000", storage_access_key="key", storage_secret_key="secret",
        )

        create_s3_client(settings)

        kwargs = boto_client.call_args.kwargs
        self.assertEqual("s3", boto_client.call_args.args[0])
        self.assertEqual("http://rustfs:9000", kwargs["endpoint_url"])
        self.assertEqual("key", kwargs["aws_access_key_id"])
        self.assertEqual("secret", kwargs["aws_secret_access_key"])
        self.assertEqual("us-east-1", kwargs["region_name"])
        self.assertEqual({"addressing_style": "path"}, kwargs["config"].s3)


if __name__ == "__main__":
    unittest.main()
