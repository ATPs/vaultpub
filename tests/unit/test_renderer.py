"""Tests for the HTML renderer."""
from __future__ import annotations

from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NavNode
from vaultpub.core.render import Renderer
from vaultpub.core.render.templates import directory_page_html, directory_sibling_files_html, nav_tree_html


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


def test_render_heading_anchors_preserve_levels_and_index_slugs(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "### **核心：`sprintf()` 函数**\n\n"
        "#### **分解 HTML/CSS 部分**:\n",
        encoding="utf-8",
    )
    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["README.md"]]

    html = renderer.render_note(note)
    toc_html = renderer.render_toc_html(note)

    assert '<h3 id="核心sprintf-函数"><strong>核心：<code>sprintf()</code> 函数</strong>' in html
    assert '<h4 id="分解-htmlcss-部分"><strong>分解 HTML/CSS 部分</strong>:' in html
    assert '<h1 id="核心sprintf-函数"' not in html
    assert 'href="#核心sprintf-函数"' in toc_html
    assert 'href="#分解-htmlcss-部分"' in toc_html


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


def test_render_note_embed_does_not_duplicate_embedded_heading_anchors(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Parent\n\n![[Child]]", encoding="utf-8")
    (tmp_path / "Child.md").write_text("# Child\n\nEmbedded content.", encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    readme = next(n for n in vault_index.notes_by_id.values() if n.stem == "README")

    html = renderer.render_note(readme)

    assert '<h1 id="parent">Parent ' in html
    assert '<h1 id="child">Child ' in html
    assert html.count('class="heading-anchor"') == 2


def test_render_local_resources_use_canonical_urls(vault_local_resources) -> None:
    config = PublisherConfig(
        vault_path=vault_local_resources,
        force_include_regexes=(r".*\.py$",),
    )
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["subdir/README.md"]]

    html = renderer.render_note(note)

    assert '<img src="/assets/subdir/image.png"' in html
    assert 'href="/assets/subdir/doc.pdf"' in html
    assert "PDF Link" in html
    assert '<a href="/assets/subdir/archive.pin.gz" download="archive.pin.gz">Archive Download</a>' in html
    assert '<a href="/assets/subdir/archive.pin.gz" download="archive.pin.gz">Archive Link</a>' in html
    assert 'href="/subdir/tool.py"' in html
    assert 'href="/subdir/Other.md"' in html
    assert 'data-embed-source="/subdir/tool.py"' in html
    assert "embedded tool" in html
    assert 'href="https://example.com"' in html
    assert 'href="#section"' in html
    assert 'href="./missing.gz"' in html
    assert 'href="./missing.txt"' in html


def test_render_raw_html_local_urls_are_rewritten(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        '# Home\n\n<img src="./image.png">\n<a href="./tool.py">Tool</a>\n',
        encoding="utf-8",
    )
    (tmp_path / "image.png").write_text("fake image", encoding="utf-8")
    (tmp_path / "tool.py").write_text("print('hello')\n", encoding="utf-8")

    config = PublisherConfig(
        vault_path=tmp_path,
        html_safe_mode=False,
        force_include_regexes=(r".*\.py$",),
    )
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = next(n for n in vault_index.notes_by_id.values() if n.stem == "README")

    html = renderer.render_note(note)

    assert '<img src="/assets/image.png">' in html
    assert 'href="/tool.py"' in html


def test_render_local_resources_decode_percent_escapes_and_fallback_parent_segments(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "Exported image 20260608223536-1.png").write_text("fake image", encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text(
        (
            "# Home\n\n"
            "![One](../attachments/Exported%20image%2020260608223536-1.png)\n\n"
            "![Two](../../../../../attachments/Exported%20image%2020260608223536-1.png)\n"
        ),
        encoding="utf-8",
    )

    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["general/README.md"]]

    html = renderer.render_note(note)

    assert html.count('/assets/attachments/Exported image 20260608223536-1.png') == 2


def test_render_local_resources_leave_missing_targets_unchanged(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "![Missing](../../../../../attachments/Exported%20image%2020260608223536-1.png)\n",
        encoding="utf-8",
    )

    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["README.md"]]

    html = renderer.render_note(note)

    assert '../attachments/Exported%20image%2020260608223536-1.png' in html


def test_render_obsidian_embed_dynamic_text_file_without_force_include(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "config.toml").write_text('name = "vaultpub"\n', encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text("![[../attachments/config.toml]]\n", encoding="utf-8")

    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["general/README.md"]]

    html = renderer.render_note(note)

    assert 'class="embed-wrapper"' in html
    assert 'data-embed-source="/assets/attachments/config.toml"' in html
    assert 'class="text-page-embed-tools"' in html
    assert 'class="topbar-code-btn"' in html
    assert 'data-code-action="toggle-wrap"' in html
    assert 'class="language-toml"' in html
    assert 'name = &quot;vaultpub&quot;' in html


def test_render_obsidian_link_dynamic_text_file_uses_asset_url(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "config.toml").write_text('name = "vaultpub"\n', encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text("[[../attachments/config.toml]]\n", encoding="utf-8")

    config = PublisherConfig(vault_path=tmp_path)
    vault_index = VaultIndexer(config).build()
    renderer = Renderer(config, vault_index)
    note = vault_index.notes_by_id[vault_index.notes_by_path["general/README.md"]]

    html = renderer.render_note(note)

    assert 'href="/assets/attachments/config.toml"' in html
    assert ">config.toml<" in html


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


def test_directory_page_renders_list_items_for_files_and_folders() -> None:
    node = NavNode(
        label="Folder",
        path="Folder",
        url="/Folder/",
        is_dir=True,
        children=[
            NavNode(label="Child", path="Folder/Child", url="/Folder/Child/", is_dir=True, children=[]),
            NavNode(label="Note.md", path="Folder/Note.md", url="/Folder/Note.md"),
        ],
    )

    html = directory_page_html(
        node,
        current_path="/Folder/",
        content_previews={"Folder/Note.md": "# Note.md\nSecond line"},
    )

    assert 'class="directory-list"' in html
    assert 'class="directory-list-item is-folder"' in html
    assert 'class="directory-list-item is-file"' in html
    assert 'directory-list-title">Child/<' in html
    assert 'directory-list-meta">Folder<' in html
    assert 'directory-list-title">Note.md<' in html
    assert 'directory-list-preview"># Note.md\nSecond line<' in html


def test_directory_sibling_files_html_lists_parent_directory_files() -> None:
    nav = NavNode(
        label="/",
        path=".",
        url="/",
        is_dir=True,
        children=[
            NavNode(label="Folder", path="Folder", url="/Folder/", is_dir=True, children=[]),
            NavNode(label="A.md", path="A.md", url="/A.md"),
            NavNode(label="README.md", path="README.md", url="/README.md"),
        ],
    )
    directory = nav.children[0]

    html = directory_sibling_files_html(nav, directory)

    assert 'class="directory-context-nav"' in html
    assert "Same Directory" in html
    assert 'href="/A.md"' in html
    assert 'href="/README.md"' in html
