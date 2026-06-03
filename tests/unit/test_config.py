"""Tests for configuration module."""
from __future__ import annotations

from pathlib import Path

from vaultpub.core.config import PublisherConfig


def test_default_config() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test-vault"))
    assert config.vault_path == Path("/tmp/test-vault").resolve()
    assert config.site_name == "vaultpub"
    assert config.url_prefix == "/"
    assert config.publish_property_mode == "publish_false_hides"


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


def test_config_exclude_folders() -> None:
    config = PublisherConfig(vault_path=Path("/tmp/test"))
    assert ".obsidian" in config.exclude_folders
    assert ".git" in config.exclude_folders
    assert "private" in config.exclude_folders
