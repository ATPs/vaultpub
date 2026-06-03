"""Tests for the HTML renderer."""
from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.render import Renderer


def test_render_note_basic(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()
    renderer = Renderer(config, vault_index)

    readme_id = vault_index.notes_by_path["README.md"]
    readme = vault_index.notes_by_id[readme_id]

    html = renderer.render_note(readme)
    assert "<h1" in html
    assert "README" in html or "Welcome" in html


def test_render_page_html_has_backlinks(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()
    renderer = Renderer(config, vault_index)

    readme_id = vault_index.notes_by_path["README.md"]
    readme = vault_index.notes_by_id[readme_id]

    html = renderer.render_page_html(readme)
    assert "Backlinks" in html or "backlinks" in html


def test_render_wikilinks_to_links(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()
    renderer = Renderer(config, vault_index)

    a_id = vault_index.notes_by_path["A.md"]
    a_note = vault_index.notes_by_id[a_id]

    html = renderer.render_note(a_note)
    # Should have transformed [[Folder/B]] to a link
    assert 'href=' in html
