"""Tests for configuration module."""
from __future__ import annotations

from pathlib import Path

import pytest

from vaultpub.core.config import ConfigError, PublisherConfig, load_config_from_yaml, normal_view_font_size


def test_default_config() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test-vault"))
    assert config.vault_path == Path("/tmp/test-vault").resolve()
    assert config.site_name == "vaultpub"
    assert config.url_prefix == "/"
    assert config.publish_property_mode == "publish_false_hides"
    assert config.strict_line_breaks is False
    assert config.show_vault_slides is True
    assert "gz" in config.allowed_attachment_types


def test_config_custom_values() -> None:
    config = PublisherConfig(
        vault_path=Path("/tmp/test"),
        site_name="My Site",
        default_theme="dark",
        font_size=18,
    )
    assert config.site_name == "My Site"
    assert config.default_theme == "dark"
    assert config.font_size == 18


@pytest.mark.parametrize(
    ("value", "expected"),
    [(12, 12), (28, 28), ("20", 20), (11, 16), (29, 16), (16.5, 16), ("large", 16), (True, 16)],
)
def test_normal_view_font_size_limits_css_values(value: object, expected: int) -> None:
    assert normal_view_font_size(value) == expected


def test_config_exclude_folders() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert ".obsidian" in config.exclude_folders
    assert ".git" in config.exclude_folders
    assert "private" in config.exclude_folders


def test_load_config_from_yaml_reads_allowed_attachment_types(tmp_path: Path) -> None:
    config_yaml = tmp_path / ".vaultpub.yml"
    config_yaml.write_text(
        "publish:\n"
        "  allowed_attachment_types:\n"
        "    - png\n"
        "    - gz\n",
        encoding="utf-8",
    )

    kwargs = load_config_from_yaml(config_yaml)

    assert kwargs["allowed_attachment_types"] == ("png", "gz")


def test_load_config_from_yaml_reads_normal_view_font_size(tmp_path: Path) -> None:
    config_yaml = tmp_path / ".vaultpub.yml"
    config_yaml.write_text("rendering:\n  font_size: 20\n", encoding="utf-8")

    kwargs = load_config_from_yaml(config_yaml)

    assert kwargs["font_size"] == 20


def test_load_config_from_yaml_reads_vault_slide_visibility(tmp_path: Path) -> None:
    config_yaml = tmp_path / ".vaultpub.yml"
    config_yaml.write_text("features:\n  vault_slides: false\n", encoding="utf-8")

    kwargs = load_config_from_yaml(config_yaml)

    assert kwargs["show_vault_slides"] is False


def test_markdown_vault_path_selects_the_file_and_uses_its_parent(tmp_path: Path) -> None:
    note = tmp_path / "Only.md"
    note.write_text("# Only", encoding="utf-8")

    config = PublisherConfig(vault_path=note)

    assert config.vault_path == tmp_path.resolve()
    assert config.entry_file == "Only.md"


@pytest.mark.parametrize("name", ["document.pdf", "missing.md"])
def test_invalid_file_vault_path_is_rejected(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    if name.endswith(".pdf"):
        path.write_bytes(b"pdf")

    with pytest.raises(ConfigError):
        PublisherConfig(vault_path=path)
