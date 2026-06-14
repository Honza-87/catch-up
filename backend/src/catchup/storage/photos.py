"""PhotoStore interface + S3-compatible implementation (boto3)."""

from __future__ import annotations

from typing import Protocol

import boto3


class PhotoStore(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under key; return the public URL."""
        ...

    def delete(self, key: str) -> None:
        """Remove the object at key (no error if absent)."""
        ...


class S3PhotoStore:
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str,
        public_base_url: str,
    ) -> None:
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def put(self, key: str, data: bytes, content_type: str) -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return f"{self._public_base_url}/{key}"

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
