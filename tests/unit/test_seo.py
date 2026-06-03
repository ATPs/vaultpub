"""Tests for SEO helpers."""
from __future__ import annotations

from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import NoteRecord
from vaultpub.core.render.seo import build_page_description, build_page_title


def test_build_page_title() -> None:
    config = PublisherConfig(vault_path=Path("/tmp"), site_name="My KB")
    note = NoteRecord(
        id="1",
        rel_path=Path("Test.md"),
        url_path="/Test",
        title="Test Page",
        stem="Test",
        excerpt="excerpt",
    )
    title = build_page_title(note, config)
    assert title == "Test Page - My KB"


def test_build_page_description_from_frontmatter() -> None:
    config = PublisherConfig(vault_path=Path("/tmp"))
    note = NoteRecord(
        id="1",
        rel_path=Path("Test.md"),
        url_path="/Test",
        title="Test",
        stem="Test",
        frontmatter={"description": "Custom SEO description"},
        excerpt="default excerpt",
    )
    desc = build_page_description(note, config)
    assert desc == "Custom SEO description"
