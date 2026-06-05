"""Tests for SEO helpers."""
from __future__ import annotations

from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import NoteRecord
from vaultpub.core.render.seo import build_meta_tags, build_page_description, build_page_title


def test_build_page_title() -> None:
    config = PublisherConfig(vault_path=Path("/tmp"), site_name="My KB")
    note = NoteRecord(
        id="1",
        rel_path=Path("Test.md"),
        url_path="/Test.md",
        title="Test Page",
        stem="Test",
        excerpt="excerpt",
    )
    title = build_page_title(note, config)
    assert title == "Test.md - My KB"


def test_build_page_description_from_frontmatter() -> None:
    config = PublisherConfig(vault_path=Path("/tmp"))
    note = NoteRecord(
        id="1",
        rel_path=Path("Test.md"),
        url_path="/Test.md",
        title="Test",
        stem="Test",
        frontmatter={"description": "Custom SEO description"},
        excerpt="default excerpt",
    )
    desc = build_page_description(note, config)
    assert desc == "Custom SEO description"


def test_build_meta_tags_escapes_attribute_values() -> None:
    config = PublisherConfig(vault_path=Path("/tmp"), site_name='KB "Docs"')
    note = NoteRecord(
        id="1",
        rel_path=Path('Fig "A".md'),
        url_path="/Fig%20%22A%22.md",
        title="Fig",
        stem="Fig",
        excerpt='sprintf("<span style=\'color:%s;\'>%s</span>", group_color, features.plot)',
    )

    html = build_meta_tags(note, config)

    assert "<title>Fig &quot;A&quot;.md - KB &quot;Docs&quot;</title>" in html
    assert 'content="sprintf(&quot;&lt;span style=&#x27;color:%s;&#x27;&gt;%s&lt;/span&gt;&quot;' in html
    assert 'content="sprintf("<span' not in html
    assert '<span style=' not in html
