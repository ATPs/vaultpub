"""Tests for path safety and URL generation."""
from __future__ import annotations

from pathlib import Path

import pytest

from vaultpub.core.exceptions import PathTraversalError
from vaultpub.core.paths import (
    generate_note_id,
    normalize_rel_path,
    rel_path_to_url_path,
    safe_join,
)


def test_safe_join_normal() -> None:
    root = Path("/tmp/vault")
    result = safe_join(root, "Folder/Note.md")
    assert result == Path("/tmp/vault/Folder/Note.md")


def test_safe_join_rejects_traversal() -> None:
    root = Path("/tmp/vault")
    with pytest.raises(PathTraversalError):
        safe_join(root, "../../etc/passwd")


def test_normalize_rel_path() -> None:
    root = Path("/tmp/vault")
    result = normalize_rel_path(Path("/tmp/vault/Folder/Note.md"), root)
    assert result == "Folder/Note.md"


def test_rel_path_to_url_path() -> None:
    assert rel_path_to_url_path("README.md") == "/README"
    assert rel_path_to_url_path("Folder/My Note.md") == "/Folder/My Note"
    assert rel_path_to_url_path("image.png") == "/image.png"


def test_generate_note_id_stable() -> None:
    id1 = generate_note_id("Folder/Note.md")
    id2 = generate_note_id("Folder/Note.md")
    assert id1 == id2
    assert len(id1) == 40  # SHA-1 hex
