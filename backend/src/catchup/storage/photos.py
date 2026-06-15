"""PhotoStore interface + S3-compatible implementation (boto3)."""

from __future__ import annotations

from typing import Protocol

import boto3


class PhotoStore(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store bytes under key in the (private) bucket."""
        ...

    def get(self, key: str) -> tuple[bytes, str]:
        """Return (bytes, content_type) for the object at key; raise if absent."""
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
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def get(self, key: str) -> tuple[bytes, str]:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"].read(), obj.get("ContentType", "application/octet-stream")

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
