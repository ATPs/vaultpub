"""Tests for vault scanner."""
from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.scanner import VaultScanner
from vaultpub.core.security import is_path_public


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


def test_scan_include_folders_root_path_includes_entire_vault(tmp_path) -> None:
    (tmp_path / "Shared").mkdir()
    (tmp_path / "README.md").write_text("# Root", encoding="utf-8")
    (tmp_path / "Shared" / "README.md").write_text("# Shared", encoding="utf-8")

    scanner = VaultScanner(PublisherConfig(vault_path=tmp_path, include_folders=(".", "Shared")))
    notes, _attachments, _text_pages, _nav = scanner.scan()

    assert {note.rel_path.as_posix() for note in notes} == {"README.md", "Shared/README.md"}


def test_scan_include_folders_can_include_all_vault_attachments(tmp_path) -> None:
    (tmp_path / "Shared").mkdir()
    (tmp_path / "private").mkdir()
    (tmp_path / "Shared" / "README.md").write_text("# Shared", encoding="utf-8")
    (tmp_path / "Shared" / "image.png").write_bytes(b"png")
    (tmp_path / "shared-image.png").write_bytes(b"png")
    (tmp_path / "private" / "secret.png").write_bytes(b"png")

    scanner = VaultScanner(
        PublisherConfig(
            vault_path=tmp_path,
            include_folders=("Shared",),
            include_all_attachments=True,
        )
    )
    notes, attachments, _text_pages, nav = scanner.scan()

    assert {note.rel_path.as_posix() for note in notes} == {"Shared/README.md"}
    assert {att.rel_path.as_posix() for att in attachments} == {"Shared/image.png", "shared-image.png"}
    assert [child.label for child in nav.children] == ["Shared"]


def test_navigation_json_controls_order_star_and_describe_direct_children(tmp_path) -> None:
    (tmp_path / "Folder").mkdir()
    (tmp_path / "A.md").write_text("# A", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B", encoding="utf-8")
    (tmp_path / "C.md").write_text("# C", encoding="utf-8")
    (tmp_path / "Folder" / "Inside.md").write_text("# Inside", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["B.md", "Folder/"]', encoding="utf-8")
    (tmp_path / "__star__.json").write_text('["C.md"]', encoding="utf-8")
    (tmp_path / "Folder" / "__category__.json").write_text(
        '{"title": "Guides", "icon": "📘", "description": "Start here", "collapsed": true}',
        encoding="utf-8",
    )

    notes, attachments, text_pages, nav = VaultScanner(PublisherConfig(vault_path=tmp_path)).scan()

    assert {note.rel_path.as_posix() for note in notes} == {"A.md", "B.md", "C.md", "Folder/Inside.md"}
    assert not attachments
    assert not text_pages
    assert [child.raw_label for child in nav.children] == ["C.md", "B.md", "Folder", "A.md"]
    assert all(child.predefined_order for child in nav.children)
    assert nav.children[0].starred
    folder = next(child for child in nav.children if child.is_dir)
    assert not folder.children[0].predefined_order
    assert folder.label == "Guides"
    assert folder.icon == "📘"
    assert folder.description == "Start here"
    assert folder.collapsed


def test_all_dunder_json_files_are_reserved_but_dunder_markdown_remains_a_note(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# README", encoding="utf-8")
    (tmp_path / "__future__.json").write_text('{"private": true}', encoding="utf-8")
    (tmp_path / "__future__.md").write_text("# Visible note", encoding="utf-8")

    notes, _attachments, _text_pages, nav = VaultScanner(PublisherConfig(vault_path=tmp_path)).scan()

    assert {note.rel_path.as_posix() for note in notes} == {"README.md", "__future__.md"}
    assert [child.raw_label for child in nav.children] == ["__future__.md", "README.md"]
    assert not is_path_public("__future__.json", None)
    assert is_path_public("__future__.md", None)
