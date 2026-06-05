"""Tests for VaultIndexer."""
from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer


def test_build_index(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()

    assert len(vault_index.notes_by_id) == 3
    assert len(vault_index.notes_by_path) == 3
    assert "README.md" in vault_index.notes_by_path

    # Check backlinks
    readme_id = vault_index.notes_by_path["README.md"]
    readme = vault_index.notes_by_id[readme_id]
    assert len(readme.backlinks) >= 1  # A links to README

    # Check nav tree
    assert vault_index.nav_tree is not None
    assert len(vault_index.nav_tree.children) > 0

    # Check search documents
    assert len(vault_index.search_documents) == 3
    assert any(doc["title"] == "README.md" for doc in vault_index.search_documents)


def test_link_resolution(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()

    a_id = vault_index.notes_by_path["A.md"]
    a_note = vault_index.notes_by_id[a_id]

    # Should have links to B and README
    assert len(a_note.outgoing_links) >= 2
    resolved = [link for link in a_note.outgoing_links if link.is_resolved]
    assert len(resolved) >= 2


def test_graph_generation(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()

    graph = vault_index.graph
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0


def test_tag_index(vault_links) -> None:
    config = PublisherConfig(vault_path=vault_links)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()

    # Alias Target has tags
    assert "project/demo" in vault_index.tags or any("demo" in t for t in vault_index.tags)


def test_heading_extraction_skips_fenced_code_blocks(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Outside\n\n```python\n# Inside code\n## Still code\n```\n\n## After code\n",
        encoding="utf-8",
    )

    config = PublisherConfig(vault_path=tmp_path)
    indexer = VaultIndexer(config)
    vault_index = indexer.build()

    note_id = vault_index.notes_by_path["README.md"]
    note = vault_index.notes_by_id[note_id]

    assert [heading.text for heading in note.headings] == ["Outside", "After code"]
