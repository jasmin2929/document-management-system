"""Storage layer: downloads the uploaded PDF documents from RustFS.

RustFS speaks the S3 protocol (like MinIO or AWS S3), so the regular AWS SDK
for Python (``boto3``) is used - the REST API does the same with the AWS SDK for Java.
The REST API uploads every file as ``documents/<uuid>.<ext>`` and puts bucket and
object key into the OCR message; this class downloads exactly that object.
"""

import logging
from typing import Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from ocr_worker.config import Settings
from ocr_worker.exceptions import StorageException

log = logging.getLogger(__name__)

# S3 error codes meaning "does not exist" (HEAD requests only return the HTTP status).
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchBucket", "404"}


def create_s3_client(settings: Settings) -> Any:
    """Create a boto3 S3 client configured for RustFS.

    Args:
        settings: Validated worker configuration (endpoint, credentials, region).

    Returns:
        A boto3 S3 client.
    """
    config = Config(
        # RustFS serves buckets as http://rustfs:9000/<bucket>, not as <bucket>.rustfs:9000 (AWS style)
        s3={"addressing_style": "path"},
        # Only send/verify checksums when S3 requires them; newer AWS defaults are not supported by every S3 server
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        connect_timeout=5,
        read_timeout=60,
        # boto3 retries transient errors (timeouts, 5xx) by itself
        retries={"max_attempts": 3, "mode": "standard"},
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,  # RustFS ignores it, but the S3 client requires one
        config=config,
    )


class ObjectStorageClient:
    """Reads documents from the S3-compatible object storage.

    Knows nothing about RabbitMQ or OCR: it only turns an object key into bytes.
    """

    def __init__(self, s3_client: Any, default_bucket: str, max_file_size: int) -> None:
        """Create the storage client.

        Args:
            s3_client: boto3 S3 client. Injected so unit tests can pass a mock instead of talking to a real RustFS.
            default_bucket: Bucket used when a message does not name one.
            max_file_size: Larger objects are refused, so a huge file cannot fill the worker's memory.
        """
        self._s3 = s3_client
        self._default_bucket = default_bucket
        self._max_file_size = max_file_size

    def check_bucket(self) -> None:
        """Check that the default bucket exists and is accessible (called once at startup).

        Raises:
            StorageException: If RustFS is not reachable or the bucket is missing.
        """
        try:
            self._s3.head_bucket(Bucket=self._default_bucket)
        except (ClientError, BotoCoreError) as ex:
            raise self._translate(ex, self._default_bucket, None) from ex

    def download(self, object_key: str, bucket: Optional[str] = None) -> bytes:
        """Download an object completely into memory.

        Args:
            object_key: Key of the object, e.g. ``"documents/3f2a...c1b.pdf"``.
            bucket: Bucket of the object; ``None`` uses the default bucket.

        Returns:
            The content of the object.

        Raises:
            StorageException: If the object does not exist, is too large or
                RustFS cannot be reached.
        """
        bucket = bucket or self._default_bucket
        try:
            response = self._s3.get_object(Bucket=bucket, Key=object_key)
            body = response["Body"]  # a stream: the content is only downloaded by read()
            try:
                size = response.get("ContentLength") or 0
                if size > self._max_file_size:
                    raise StorageException(
                        f"Object '{object_key}' is too large ({size} bytes, limit {self._max_file_size} bytes)"
                    )
                content = body.read()
            finally:
                body.close()  # releases the HTTP connection
        except (ClientError, BotoCoreError) as ex:
            raise self._translate(ex, bucket, object_key) from ex

        log.info("Downloaded '%s/%s' from object storage (%d bytes)", bucket, object_key, len(content))
        return content

    @staticmethod
    def _translate(ex: Exception, bucket: str, object_key: Optional[str]) -> StorageException:
        """Turn a boto3 error into this layer's exception, so callers do not depend on boto3."""
        target = f"'{bucket}/{object_key}'" if object_key else f"bucket '{bucket}'"
        if isinstance(ex, ClientError):
            code = ex.response.get("Error", {}).get("Code", "")
            if code in _NOT_FOUND_CODES:
                return StorageException(f"{target} does not exist in the object storage")
            return StorageException(f"Object storage refused access to {target}: {code or ex}")
        # BotoCoreError: no HTTP answer at all (RustFS down, DNS, timeout, ...)
        return StorageException(f"Object storage not reachable while reading {target}: {ex}")
