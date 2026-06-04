"""Tests for the HTML renderer."""
from __future__ import annotations

from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NavNode
from vaultpub.core.render import Renderer
from vaultpub.core.render.templates import nav_tree_html


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
    assert 'href="/Folder/B.md"' in html
    assert 'class="internal-link"' in html


def test_render_obsidian_syntax_outputs_real_html(vault_obsidian_syntax) -> None:
    config = PublisherConfig(vault_path=vault_obsidian_syntax)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)

    def render(stem: str) -> str:
        note = next(n for n in vault_index.notes_by_id.values() if n.stem == stem)
        return renderer.render_note(note)

    embeds = render("Embeds")
    assert '<img src="/assets/image.png"' in embeds
    assert "&lt;!-- VAULTPUB" not in embeds

    callouts = render("Callouts")
    assert callouts.count('class="callout"') == 4
    assert 'data-callout="tip"' in callouts

    mermaid = render("Mermaid")
    assert '<div class="mermaid">' in mermaid
    assert "language-mermaid" not in mermaid

    math = render("Math")
    assert 'class="math inline"' in math
    assert 'class="math block"' in math


def test_render_strips_frontmatter(vault_links) -> None:
    config = PublisherConfig(vault_path=vault_links)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = next(n for n in vault_index.notes_by_id.values() if n.stem == "Alias Target")

    html = renderer.render_note(note)

    assert "aliases:" not in html
    assert "project/demo" not in html
    assert "This note has aliases." in html


def test_render_note_embed_renders_target_body(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Home\n\n![[Child]]", encoding="utf-8")
    (tmp_path / "Child.md").write_text("# Child\n\nEmbedded content.", encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    readme = next(n for n in vault_index.notes_by_id.values() if n.stem == "README")

    html = renderer.render_note(readme)

    assert 'class="embed-wrapper"' in html
    assert "Embedded content." in html


def test_nav_tree_omits_root_directory() -> None:
    nav = NavNode(
        label="/",
        path=".",
        url="/",
        is_dir=True,
        children=[
            NavNode(
                label="Folder",
                path="Folder",
                url="/Folder/",
                is_dir=True,
                children=[
                    NavNode(label="Child.md", path="Folder/Child.md", url="/Folder/Child.md"),
                ],
            ),
            NavNode(label="README.md", path="README.md", url="/README.md"),
        ],
    )

    html = "<ul>" + nav_tree_html(nav) + "</ul>"

    assert "<summary>/</summary>" not in html
    assert 'href="/Folder/"' in html
    assert "Folder/" in html
    assert 'href="/README.md"' in html
