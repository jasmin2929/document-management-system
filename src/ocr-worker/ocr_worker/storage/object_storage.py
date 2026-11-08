"""Downloads the uploaded documents from RustFS via the S3 API (boto3)."""

import logging
from typing import Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from ocr_worker.config import Settings
from ocr_worker.exceptions import StorageException

log = logging.getLogger(__name__)

# HEAD requests only return the HTTP status, hence "404".
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchBucket", "404"}


def create_s3_client(settings: Settings) -> Any:
    config = Config(
        # RustFS serves http://rustfs:9000/<bucket>, not <bucket>.rustfs:9000
        s3={"addressing_style": "path"},
        # newer boto3 checksum defaults are not supported by every S3 server
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        connect_timeout=5,
        read_timeout=60,
        retries={"max_attempts": 3, "mode": "standard"},
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,
        config=config,
    )


class ObjectStorageClient:
    def __init__(self, s3_client: Any, default_bucket: str, max_file_size: int) -> None:
        self._s3 = s3_client
        self._default_bucket = default_bucket
        self._max_file_size = max_file_size

    def check_bucket(self) -> None:
        try:
            self._s3.head_bucket(Bucket=self._default_bucket)
        except (ClientError, BotoCoreError) as ex:
            raise self._translate(ex, self._default_bucket, None) from ex

    def download(self, object_key: str, bucket: Optional[str] = None) -> bytes:
        bucket = bucket or self._default_bucket
        try:
            response = self._s3.get_object(Bucket=bucket, Key=object_key)
            body = response["Body"]
            try:
                # Check the size before read(), so a huge file never ends up in memory.
                size = response.get("ContentLength") or 0
                if size > self._max_file_size:
                    raise StorageException(
                        f"Object '{object_key}' is too large ({size} bytes, limit {self._max_file_size} bytes)"
                    )
                content = body.read()
            finally:
                body.close()
        except (ClientError, BotoCoreError) as ex:
            raise self._translate(ex, bucket, object_key) from ex

        log.info("Downloaded '%s/%s' from object storage (%d bytes)", bucket, object_key, len(content))
        return content

    @staticmethod
    def _translate(ex: Exception, bucket: str, object_key: Optional[str]) -> StorageException:
        target = f"'{bucket}/{object_key}'" if object_key else f"bucket '{bucket}'"
        if isinstance(ex, ClientError):
            code = ex.response.get("Error", {}).get("Code", "")
            if code in _NOT_FOUND_CODES:
                return StorageException(f"{target} does not exist in the object storage")
            return StorageException(f"Object storage refused access to {target}: {code or ex}")
        # BotoCoreError: no HTTP answer at all (RustFS down, DNS, timeout)
        return StorageException(f"Object storage not reachable while reading {target}: {ex}")
