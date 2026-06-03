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
    """Convert a file-relative path to a URL-friendly path (strip .md, keep dir structure).

    Examples:
        Folder/My Note.md -> Folder/My Note
        README.md -> README
    """
    pp = PurePosixPath(rel_path)
    if pp.suffix == ".md":
        pp = pp.with_suffix("")
    return "/" + pp.as_posix()


def url_path_to_rel_path(url_path: str) -> str:
    """Convert a URL path back to relative vault path (add .md extension)."""
    pp = PurePosixPath(url_path.lstrip("/"))
    if not pp.suffix:
        return str(pp) + ".md"
    return str(pp)


def generate_note_id(rel_path: str) -> str:
    """Generate a stable ID for a note from its relative path.

    Uses SHA-1 of the POSIX relative path for consistency.
    """
    import hashlib

    return hashlib.sha1(rel_path.encode()).hexdigest()
