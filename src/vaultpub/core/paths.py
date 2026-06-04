from __future__ import annotations

from pathlib import Path, PurePosixPath

from vaultpub.core.exceptions import PathTraversalError


def safe_join(vault_root: Path, rel: str) -> Path:
    """Join a relative path to vault root, ensuring no traversal outside root."""
    candidate = (vault_root / rel).resolve()
    root = vault_root.resolve()
    if not candidate.is_relative_to(root):
        raise PathTraversalError(f"Path escapes vault root: {rel!r}")
    return candidate


def normalize_rel_path(file_path: Path, vault_root: Path) -> str:
    """Return a POSIX relative path from vault root to file_path."""
    try:
        rel = file_path.resolve().relative_to(vault_root.resolve())
    except ValueError:
        raise PathTraversalError(f"File outside vault: {file_path}") from None
    return rel.as_posix()


def rel_path_to_url_path(rel_path: str) -> str:
    """Convert a file-relative path to a public file URL.

    Examples:
        Folder/My Note.md -> /Folder/My Note.md
        README.md -> /README.md
    """
    return "/" + PurePosixPath(rel_path).as_posix()


def directory_path_to_url_path(rel_path: str) -> str:
    """Convert a relative directory path to a public directory URL."""
    normalized = PurePosixPath(rel_path).as_posix().strip("/")
    if not normalized or normalized == ".":
        return "/"
    return f"/{normalized}/"


def url_path_to_rel_path(url_path: str) -> str:
    """Convert a file URL path back to a relative vault path."""
    return PurePosixPath(url_path.lstrip("/")).as_posix()


def file_display_name(rel_path: str | PurePosixPath) -> str:
    """Return the filename, including extension, for system-generated labels."""
    return PurePosixPath(rel_path).name


def directory_display_name(rel_path: str | PurePosixPath) -> str:
    """Return the final directory segment for system-generated labels."""
    normalized = PurePosixPath(rel_path)
    if normalized.as_posix() in ("", "."):
        return "/"
    return normalized.name


def static_html_url(url_path: str) -> str:
    """Convert a logical page URL to the static-build URL that serves HTML directly."""
    if url_path == "/":
        return "/index.html"
    if url_path.endswith("/"):
        return f"{url_path}index.html"
    return f"{url_path}.html"


def generate_note_id(rel_path: str) -> str:
    """Generate a stable ID for a note from its relative path.

    Uses SHA-1 of the POSIX relative path for consistency.
    """
    import hashlib

    return hashlib.sha1(rel_path.encode()).hexdigest()
