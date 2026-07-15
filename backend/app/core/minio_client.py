"""
AION MinIO Client — S3-Compatible Object Storage
Handles documents, attachments, and large binary objects
"""
from __future__ import annotations

import io
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_minio_client: Optional[Minio] = None

BUCKETS = {
    "documents": "aion-documents",
    "attachments": "aion-attachments",
    "reports": "aion-reports",
    "exports": "aion-exports",
    "avatars": "aion-avatars",
}


def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _minio_client


async def init_buckets() -> None:
    """Ensure all required buckets exist."""
    client = get_minio_client()
    for bucket_key, bucket_name in BUCKETS.items():
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                logger.info("Created MinIO bucket", bucket=bucket_name)
            else:
                logger.debug("MinIO bucket exists", bucket=bucket_name)
        except S3Error as e:
            logger.error("Failed to create MinIO bucket", bucket=bucket_name, error=str(e))
            raise


async def upload_file(
    bucket_key: str,
    object_name: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    metadata: Optional[dict] = None,
) -> str:
    """Upload a file to MinIO. Returns the object URL."""
    client = get_minio_client()
    bucket_name = BUCKETS[bucket_key]
    data_stream = io.BytesIO(data)
    client.put_object(
        bucket_name,
        object_name,
        data_stream,
        length=len(data),
        content_type=content_type,
        metadata=metadata,
    )
    logger.info("Uploaded file to MinIO", bucket=bucket_name, object=object_name)
    return f"{bucket_name}/{object_name}"


async def download_file(bucket_key: str, object_name: str) -> bytes:
    """Download a file from MinIO. Returns raw bytes."""
    client = get_minio_client()
    bucket_name = BUCKETS[bucket_key]
    response = client.get_object(bucket_name, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


async def delete_file(bucket_key: str, object_name: str) -> None:
    """Delete an object from MinIO."""
    client = get_minio_client()
    bucket_name = BUCKETS[bucket_key]
    client.remove_object(bucket_name, object_name)
    logger.info("Deleted file from MinIO", bucket=bucket_name, object=object_name)


def get_presigned_url(bucket_key: str, object_name: str, expires_hours: int = 1) -> str:
    """Generate a presigned URL for temporary file access."""
    from datetime import timedelta
    client = get_minio_client()
    bucket_name = BUCKETS[bucket_key]
    return client.presigned_get_object(
        bucket_name, object_name, expires=timedelta(hours=expires_hours)
    )


async def close_minio() -> None:
    global _minio_client
    _minio_client = None
    logger.info("MinIO client closed")
