"""File storage service for event photo uploads."""

import logging
import uuid
from pathlib import Path

import magic
from fastapi import UploadFile

logger = logging.getLogger(__name__)

UPLOAD_ROOT = Path("/data/uploads")

# 10 MB default max
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Extension mapping for validated MIME types
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class FileStorageError(Exception):
    """Raised for file storage validation/IO errors."""


def _ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def validate_mime_type(content: bytes) -> str:
    """Validate file content using magic bytes. Returns MIME type or raises."""
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise FileStorageError(
            f"File type '{mime_type}' is not allowed. Accepted types: JPEG, PNG, WebP"
        )
    return mime_type


async def save_upload(
    file: UploadFile,
    family_id: str,
    event_id: str,
) -> tuple[str, str, int, str]:
    """Save an uploaded file to disk.

    Returns:
        Tuple of (filename, relative_path, file_size, mime_type)
    """
    # Read in chunks to reject oversized files without buffering everything
    chunk_size = 64 * 1024  # 64 KB
    chunks: list[bytes] = []
    file_size = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise FileStorageError(
                f"File too large (>{MAX_FILE_SIZE / 1024 / 1024:.0f} MB). "
                f"Maximum is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
            )
        chunks.append(chunk)

    content = b"".join(chunks)

    if file_size == 0:
        raise FileStorageError("File is empty")

    # Validate via magic bytes
    mime_type = validate_mime_type(content)
    ext = MIME_TO_EXT[mime_type]

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    relative_dir = f"{family_id}/events/{event_id}/photos"
    relative_path = f"{relative_dir}/{unique_name}"
    full_dir = UPLOAD_ROOT / relative_dir

    _ensure_dir(full_dir)

    full_path = UPLOAD_ROOT / relative_path
    full_path.write_bytes(content)

    original_name = file.filename or unique_name
    logger.info(
        "Saved upload: %s -> %s (%d bytes, %s)",
        original_name,
        relative_path,
        file_size,
        mime_type,
    )

    return original_name, relative_path, file_size, mime_type


def delete_file(relative_path: str) -> bool:
    """Delete a file from disk. Returns True if deleted, False if not found."""
    full_path = UPLOAD_ROOT / relative_path
    if full_path.exists():
        full_path.unlink()
        logger.info("Deleted file: %s", relative_path)
        return True
    logger.warning("File not found for deletion: %s", relative_path)
    return False


def get_upload_url(relative_path: str) -> str:
    """Convert a relative file path to a URL path."""
    return f"/uploads/{relative_path}"
