"""Tests for security module."""
from __future__ import annotations

from pathlib import Path

import pytest

from vaultpub.core.exceptions import PathTraversalError
from vaultpub.core.paths import safe_join
from vaultpub.core.security import is_path_public


def test_safe_join_blocks_traversal() -> None:
    root = Path("/tmp/vault").resolve()
    with pytest.raises(PathTraversalError):
        safe_join(root, "../../etc/passwd")


def test_safe_join_blocks_absolute_symlink_escape() -> None:
    root = Path("/tmp/vault").resolve()
    with pytest.raises(PathTraversalError):
        safe_join(root, "/etc/passwd")


def test_is_path_public_hidden() -> None:
    assert not is_path_public(".obsidian/workspace.json", None)
    assert not is_path_public(".git/config", None)
    assert not is_path_public("folder/.hidden", None)


def test_is_path_public_normal() -> None:
    assert is_path_public("README.md", None)
    assert is_path_public("Folder/Note.md", None)


def test_is_path_public_forbidden_names() -> None:
    assert not is_path_public("metadata.json", None)
    assert not is_path_public(".vaultpub.yml", None)
