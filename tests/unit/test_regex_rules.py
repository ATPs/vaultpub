"""Tests for regex-based force-include and force-exclude patterns."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from vaultpub.core.config import PublisherConfig, _compile_regexes
from vaultpub.core.exceptions import ConfigError
from vaultpub.core.scanner import VaultScanner
from vaultpub.core.security import is_force_included, is_path_excluded, is_path_public


# ── Config validation ──────────────────────────────────────────────────

def test_force_include_regexes_default() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert config.force_include_regexes == ()
    assert config.force_exclude_regexes == ()


def test_force_include_regexes_from_kwarg() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"), force_include_regexes=(".*\\.py$",))
    assert config.force_include_regexes == (".*\\.py$",)
    compiled = getattr(config, "_compiled_force_include", [])
    assert len(compiled) == 1


def test_force_exclude_regexes_from_kwarg() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_exclude_regexes=("(^|/)secret(/|$)",),
    )
    assert config.force_exclude_regexes == ("(^|/)secret(/|$)",)
    compiled = getattr(config, "_compiled_force_exclude", [])
    assert len(compiled) == 1


def test_invalid_regex_raises_config_error() -> None:
    with pytest.raises(ConfigError, match="Invalid regex"):
        PublisherConfig(vault_path=Path("/tmp/test"), force_include_regexes=("***[_]invalid",))


def test_invalid_regex_in_exclude_raises_config_error() -> None:
    with pytest.raises(ConfigError, match="Invalid regex"):
        PublisherConfig(vault_path=Path("/tmp/test"), force_exclude_regexes=("[open",))


def test_invalid_glob_like_pattern_raises() -> None:
    # Patterns like "*\\.py" (glob form) should raise ConfigError — the backslash-dot is unescaped in regex
    with pytest.raises(ConfigError, match="Invalid regex"):
        PublisherConfig(vault_path=Path("/tmp/test"), force_include_regexes=("*\\.py",))


# ── is_path_excluded ───────────────────────────────────────────────────

def test_is_path_excluded_force_exclude_regex_file() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_exclude_regexes=("secret",),
    )
    assert is_path_excluded("secret-plan.md", config)
    assert is_path_excluded("research/secret-plan.md", config)
    assert not is_path_excluded("normal.md", config)


def test_is_path_excluded_force_exclude_regex_folder() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_exclude_regexes=("(^|/)private(/|$)",),
    )
    assert is_path_excluded("private/Note.md", config)
    assert is_path_excluded("private/sub/deep.md", config)
    assert not is_path_excluded("not-private/Note.md", config)


def test_is_path_excluded_force_exclude_attachment() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_exclude_regexes=("\\.private\\.(png|jpg)$",),
    )
    assert is_path_excluded("images/diagram.private.png", config)
    assert not is_path_excluded("images/diagram.png", config)


def test_is_path_excluded_exclude_wins_over_include() -> None:
    """force_exclude_regexes wins when both match the same path."""
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_include_regexes=("scripts/.*",),
        force_exclude_regexes=("scripts/secret",),
    )
    assert is_path_excluded("scripts/secret/keys.py", config)
    assert is_path_excluded("scripts/secret-tool.py", config)


def test_is_path_excluded_hidden_still_excluded() -> None:
    """Hidden files remain excluded regardless of regex config."""
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_include_regexes=(".*",),  # match everything
    )
    assert is_path_excluded(".hidden/secret.md", config)
    assert is_path_excluded(".secret.md", config)


def test_is_path_excluded_hidden_file_access_bypasses_hidden() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        hidden_file_access=True,
    )
    assert not is_path_excluded(".notes/visible.md", config)


def test_is_path_excluded_hidden_file_access_not_bypass_force_exclude() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        hidden_file_access=True,
        force_exclude_regexes=("private",),
    )
    assert is_path_excluded("private/secret.md", config)


def test_is_path_excluded_always_forbidden() -> None:
    """Always-forbidden paths are excluded regardless of any config."""
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        hidden_file_access=True,
        force_include_regexes=(".*",),
    )
    assert is_path_excluded(".git/config", config)
    assert is_path_excluded(".obsidian/workspace.json", config)
    assert is_path_excluded("metadata.json", config)
    assert is_path_excluded(".vaultpub.yml", config)


def test_is_path_excluded_exclude_globs_still_works() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        exclude_globs=("**/*.draft.md",),
    )
    assert is_path_excluded("notes/my.draft.md", config)


def test_is_path_excluded_exclude_folders_still_works() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        exclude_folders=("trash",),
    )
    assert is_path_excluded("trash/old.md", config)


# ── is_force_included ──────────────────────────────────────────────────

def test_is_force_included_matches_py_file() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_include_regexes=(".*\\.py$",),
    )
    assert is_force_included("scripts/tool.py", config)
    assert not is_force_included("scripts/tool.md", config)


def test_is_force_included_no_patterns_returns_false() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert not is_force_included("scripts/tool.py", config)


def test_is_force_included_empty_patterns() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        force_include_regexes=(),
    )
    assert not is_force_included("anything.py", config)


# ── is_path_public backward compat ─────────────────────────────────────

def test_is_path_public_normal() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert is_path_public("README.md", config)
    assert is_path_public("Folder/Note.md", config)


def test_is_path_public_hidden() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert not is_path_public(".hidden/file.md", config)
    assert not is_path_public("folder/.hidden/file.md", config)


# ── Scanner integration ────────────────────────────────────────────────

def test_scanner_force_exclude_regex_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        (vault / "secret-plan.md").write_text("# secret")

        config = PublisherConfig(
            vault_path=vault,
            force_exclude_regexes=("secret",),
        )
        scanner = VaultScanner(config)
        notes, _, _, _ = scanner.scan()

        titles = {n.title for n in notes}
        assert "README" in titles
        assert "secret-plan" not in titles


def test_scanner_force_exclude_regex_folder() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        private = vault / "private"
        private.mkdir()
        (private / "note.md").write_text("# private")

        config = PublisherConfig(
            vault_path=vault,
            force_exclude_regexes=("(^|/)private(/|$)",),
        )
        scanner = VaultScanner(config)
        notes, _, _, _ = scanner.scan()

        titles = {n.title for n in notes}
        assert "README" in titles
        assert "note" not in titles


def test_scanner_force_exclude_attachment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        img_dir = vault / "images"
        img_dir.mkdir()
        (img_dir / "diagram.png").write_text("fake png")  # not real PNG but ext matches
        (img_dir / "diagram.private.png").write_text("fake png")

        config = PublisherConfig(
            vault_path=vault,
            force_exclude_regexes=("\\.private\\.(png|jpg)$",),
        )
        scanner = VaultScanner(config)
        _, attachments, _, _ = scanner.scan()

        rels = {a.rel_path.as_posix() for a in attachments}
        assert "images/diagram.png" in rels
        assert "images/diagram.private.png" not in rels


def test_scanner_force_include_py_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        (vault / "scripts").mkdir()
        (vault / "scripts" / "tool.py").write_text("print('hello')")

        config = PublisherConfig(
            vault_path=vault,
            force_include_regexes=(".*\\.py$",),
        )
        scanner = VaultScanner(config)
        notes, _, text_pages, _ = scanner.scan()

        assert len(notes) == 1  # README.md only
        assert len(text_pages) == 1
        assert text_pages[0].stem == "tool"
        assert text_pages[0].language == "python"
        assert text_pages[0].raw_text == "print('hello')"
        assert text_pages[0].url_path == "/scripts/tool.py"


def test_scanner_force_include_exclude_wins() -> None:
    """When both force-include and force-exclude match, exclude wins."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        scripts = vault / "scripts"
        scripts.mkdir()
        (scripts / "tool.py").write_text("print('hello')")
        (scripts / "secret.py").write_text("TOKEN='xxx'")

        config = PublisherConfig(
            vault_path=vault,
            force_include_regexes=(".*\\.py$",),
            force_exclude_regexes=("secret",),
        )
        scanner = VaultScanner(config)
        _, _, text_pages, _ = scanner.scan()

        stems = {t.stem for t in text_pages}
        assert "tool" in stems
        assert "secret" not in stems


def test_scanner_force_include_skips_binary() -> None:
    """Non-text files matched by force-include regex are rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        (vault / "data.bin").write_bytes(b"\x00\x01\x02\xff\xfe\xfd")

        config = PublisherConfig(
            vault_path=vault,
            force_include_regexes=(".*\\.bin$",),
        )
        scanner = VaultScanner(config)
        _, _, text_pages, _ = scanner.scan()

        assert len(text_pages) == 0


def test_scanner_hidden_still_excluded_with_force_include() -> None:
    """Hidden files remain excluded even with force_include_regexes."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / ".hidden").mkdir()
        (vault / ".hidden" / "script.py").write_text("print('hidden')")

        config = PublisherConfig(
            vault_path=vault,
            force_include_regexes=(".*\\.py$",),
        )
        scanner = VaultScanner(config)
        _, _, text_pages, _ = scanner.scan()

        assert len(text_pages) == 0


def test_scanner_force_include_text_file_appears_in_nav() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "README.md").write_text("# README")
        (vault / "scripts").mkdir()
        (vault / "scripts" / "tool.py").write_text("print('hello')")

        config = PublisherConfig(
            vault_path=vault,
            force_include_regexes=(".*\\.py$",),
        )
        scanner = VaultScanner(config)
        _, _, text_pages, nav = scanner.scan()

        # Find tool.py in nav
        def _find_node(node, label):
            for child in node.children:
                if child.label == label:
                    return child
                if child.is_dir:
                    found = _find_node(child, label)
                    if found:
                        return found
            return None

        tool_node = _find_node(nav, "tool")
        assert tool_node is not None
        assert tool_node.url == "/scripts/tool.py"


def test_scanner_text_page_excluded_by_exclude_folder() -> None:
    """exclude_folders also excludes force-included files in those folders."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "private").mkdir()
        (vault / "private" / "script.py").write_text("print('secret')")

        config = PublisherConfig(
            vault_path=vault,
            exclude_folders=("private",),
            force_include_regexes=(".*\\.py$",),
        )
        scanner = VaultScanner(config)
        _, _, text_pages, _ = scanner.scan()

        assert len(text_pages) == 0
