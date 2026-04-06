"""Cloudflare R2 storage helpers for the Voice Clone feature.

This module provides a simple interface to upload, download, and generate presigned URLs
for Cloudflare R2 object storage, which replaces local disk storage for voice clone
artifacts (datasets, trained models, conversion inputs/outputs).

Env vars (from .env example):
    R2_ACCOUNT_ID         - Cloudflare account ID.
    R2_ACCESS_KEY_ID     - R2 access key ID.
    R2_SECRET_ACCESS_KEY - R2 secret access key.
    R2_BUCKET_NAME       - R2 bucket name (e.g. audiocraft-vc).
    R2_ENDPOINT_URL      - S3-compatible endpoint URL.
    R2_PUBLIC_BASE_URL   - Optional public URL for direct bucket access.
"""
from __future__ import annotations

import logging
import os
from typing import BinaryIO

import boto3
from botocore.config import Config

log = logging.getLogger(__name__)

# Lazy client singleton
_client: boto3.client | None = None


def _get_client() -> boto3.client:
    """Return a reusable S3 client configured for R2."""
    global _client
    if _client is None:
        _client = boto3.client(
            's3',
            endpoint_url=os.environ['R2_ENDPOINT_URL'],
            aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
            config=Config(signature_version='s3v4'),
            region_name='auto',
        )
    return _client


def _bucket() -> str:
    return os.environ['R2_BUCKET_NAME']


def upload_bytes(r2_key: str, data: bytes, content_type: str = 'application/octet-stream') -> None:
    """Upload raw bytes to R2.

    Args:
        r2_key: Object key (e.g. "vc/users/{uid}/profiles/{pid}/dataset/file.wav").
        data: Raw file bytes.
        content_type: MIME type (default: octet-stream).
    """
    _get_client().put_object(
        Bucket=_bucket(),
        Key=r2_key,
        Body=data,
        ContentType=content_type,
    )


def upload_fileobj(r2_key: str, fileobj: BinaryIO, content_type: str = 'application/octet-stream',
                 length: int | None = None) -> None:
    """Upload a file-like object to R2.

    Args:
        r2_key: Object key.
        fileobj: File-like object with read() method.
        content_type: MIME type.
        length: Optional content-length for progress handling.
    """
    extra_args = {}
    if length is not None:
        extra_args['ContentLength'] = length

    _get_client().upload_fileobj(
        fileobj,
        Bucket=_bucket(),
        Key=r2_key,
        ExtraArgs={'ContentType': content_type, **extra_args},
    )


def download_bytes(r2_key: str) -> bytes:
    """Download object contents as bytes.

    Args:
        r2_key: Object key.

    Returns:
        Raw file bytes.
    """
    response = _get_client().get_object(
        Bucket=_bucket(),
        Key=r2_key,
    )
    return response['Body'].read()


def download_stream(r2_key: str) -> BinaryIO:
    """Return a file-like stream for streaming download.

    Use this when you need to stream large files without loading into memory.

    Args:
        r2_key: Object key.

    Returns:
        A file-like object (Body member of the S3 response). MUST be closed by caller.
    """
    response = _get_client().get_object(
        Bucket=_bucket(),
        Key=r2_key,
    )
    return response['Body']


def delete_object(r2_key: str) -> None:
    """Delete an object from R2.

    Args:
        r2_key: Object key.
    """
    _get_client().delete_object(
        Bucket=_bucket(),
        Key=r2_key,
    )


def object_exists(r2_key: str) -> bool:
    """Check if an object exists in the bucket.

    Args:
        r2_key: Object key.

    Returns:
        True if the object exists, False otherwise.
    """
    client = _get_client()
    try:
        client.head_object(Bucket=_bucket(), Key=r2_key)
        return True
    except client.exceptions.NoSuchKey:
        return False


def presigned_get_url(r2_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned GET URL for direct browser download.

    Args:
        r2_key: Object key.
        expires_in: URL validity in seconds (default 1 hour).

    Returns:
        Presigned URL string.
    """
    return _get_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': _bucket(), 'Key': r2_key},
        ExpiresIn=expires_in,
    )


def presigned_put_url(r2_key: str, content_type: str = 'application/octet-stream',
                      expires_in: int = 3600) -> str:
    """Generate a presigned PUT URL for direct browser upload.

    This allows the browser to upload directly to R2 without going through
    the Flask server, which is useful for large files.

    Args:
        r2_key: Object key that will be created.
        content_type: Expected MIME type.
        expires_in: URL validity in seconds (default 1 hour).

    Returns:
        Presigned URL string.
    """
    return _get_client().generate_presigned_url(
        'put_object',
        Params={
            'Bucket': _bucket(),
            'Key': r2_key,
            'ContentType': content_type,
        },
        ExpiresIn=expires_in,
    )


def public_url(r2_key: str) -> str | None:
    """Return the public (CDN) URL for an object, if configured.

    Returns None if R2_PUBLIC_BASE_URL is not set.

    Args:
        r2_key: Object key.

    Returns:
        Full public URL, or None if not configured.
    """
    base = os.environ.get('R2_PUBLIC_BASE_URL')
    if not base:
        return None
    return f"{base.rstrip('/')}/{r2_key.lstrip('/')}"