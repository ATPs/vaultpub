"""Tests for vault scanner."""
from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.scanner import VaultScanner


def test_scan_basic_vault(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    scanner = VaultScanner(config)
    notes, attachments, _text_pages, nav = scanner.scan()

    assert len(notes) == 3  # README, A, Folder/B
    assert len(attachments) == 0

    rel_paths = {n.rel_path.as_posix() for n in notes}
    assert "README.md" in rel_paths
    assert "A.md" in rel_paths
    assert "Folder/B.md" in rel_paths


def test_scan_excludes_hidden() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        (vault / ".hidden").mkdir()
        (vault / ".hidden" / "secret.md").write_text("# secret")

        config = PublisherConfig(vault_path=vault)
        scanner = VaultScanner(config)
        notes, _, _, _ = scanner.scan()

        rel_paths = {n.rel_path.as_posix() for n in notes}
        assert "README.md" in rel_paths
        assert ".hidden/secret.md" not in rel_paths


def test_scan_publish_false_hides(vault_publish_filters) -> None:
    config = PublisherConfig(vault_path=vault_publish_filters)
    scanner = VaultScanner(config)
    notes, _, _, _ = scanner.scan()

    titles = {n.title for n in notes}
    assert "README" in titles
    assert "Public" in titles
    assert "Forced" in titles
    assert "Draft" not in titles


def test_resolve_home(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    scanner = VaultScanner(config)
    notes, _, _, _ = scanner.scan()
    home = scanner.resolve_home(notes)
    assert home is not None
    assert home.stem == "README"


def test_scan_default_config_includes_gz_attachments(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# README", encoding="utf-8")
    (tmp_path / "archive.pin.gz").write_text("fake archive", encoding="utf-8")

    scanner = VaultScanner(PublisherConfig(vault_path=tmp_path))
    _notes, attachments, _text_pages, _nav = scanner.scan()

    rel_paths = {att.rel_path.as_posix() for att in attachments}
    assert "archive.pin.gz" in rel_paths


def test_scan_include_folders_scopes_notes_attachments_and_nav(tmp_path) -> None:
    (tmp_path / "Shared").mkdir()
    (tmp_path / "Private").mkdir()
    (tmp_path / "Shared" / "README.md").write_text("# Shared", encoding="utf-8")
    (tmp_path / "Shared" / "image.png").write_bytes(b"png")
    (tmp_path / "Private" / "Secret.md").write_text("# Secret", encoding="utf-8")

    scanner = VaultScanner(PublisherConfig(vault_path=tmp_path, include_folders=("Shared",)))
    notes, attachments, _text_pages, nav = scanner.scan()

    assert {note.rel_path.as_posix() for note in notes} == {"Shared/README.md"}
    assert {att.rel_path.as_posix() for att in attachments} == {"Shared/image.png"}
    assert [child.label for child in nav.children] == ["Shared"]
