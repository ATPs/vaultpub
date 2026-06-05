from __future__ import annotations

from pathlib import PurePosixPath

IMAGE_ATTACHMENT_TYPES = frozenset({"png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico"})
AUDIO_ATTACHMENT_TYPES = frozenset({"mp3", "wav", "ogg", "flac", "m4a"})
VIDEO_ATTACHMENT_TYPES = frozenset({"mp4", "webm", "mov", "avi"})
INLINEABLE_ATTACHMENT_TYPES = frozenset({
    *IMAGE_ATTACHMENT_TYPES,
    *AUDIO_ATTACHMENT_TYPES,
    *VIDEO_ATTACHMENT_TYPES,
    "pdf",
})
DOWNLOAD_ATTACHMENT_TYPES = frozenset({"gz", "tgz", "zip", "tar", "bz2", "xz", "7z"})
DEFAULT_ATTACHMENT_TYPES = (
    "png", "jpg", "jpeg", "gif", "svg", "webp",
    "pdf", "mp3", "wav", "ogg", "mp4", "webm",
    "gz", "tgz", "zip", "tar", "bz2", "xz", "7z",
)

_MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "ico": "image/x-icon",
    "pdf": "application/pdf",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "gz": "application/gzip",
    "tgz": "application/gzip",
    "zip": "application/zip",
    "tar": "application/x-tar",
    "bz2": "application/x-bzip2",
    "xz": "application/x-xz",
    "7z": "application/x-7z-compressed",
}


def attachment_ext(rel_path: str | PurePosixPath) -> str:
    return PurePosixPath(rel_path).suffix.lower().lstrip(".")


def attachment_mime_type(rel_path: str | PurePosixPath) -> str:
    return _MIME_TYPES.get(attachment_ext(rel_path), "application/octet-stream")


def is_image_attachment(rel_path: str | PurePosixPath) -> bool:
    return attachment_ext(rel_path) in IMAGE_ATTACHMENT_TYPES


def is_inlineable_attachment(rel_path: str | PurePosixPath) -> bool:
    return attachment_ext(rel_path) in INLINEABLE_ATTACHMENT_TYPES


def is_download_only_attachment(rel_path: str | PurePosixPath) -> bool:
    return attachment_ext(rel_path) not in INLINEABLE_ATTACHMENT_TYPES


def attachment_download_name(rel_path: str | PurePosixPath) -> str:
    return PurePosixPath(rel_path).name


def attachment_content_disposition(rel_path: str | PurePosixPath) -> str:
    filename = attachment_download_name(rel_path).replace("\\", "").replace('"', "")
    return f'attachment; filename="{filename}"'
