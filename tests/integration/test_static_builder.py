"""Integration tests for StaticSiteBuilder."""
from __future__ import annotations

import tempfile
from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.export import StaticSiteBuilder


def test_build_static_site(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    builder = StaticSiteBuilder(config)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "public"
        result = builder.build(out)
        assert result.pages_written > 0
        assert (out / "index.html").exists()
        assert (out / "README.md.html").exists()
        assert (out / "Folder" / "index.html").exists()
        assert (out / "search-index.json").exists()
        assert (out / "graph.json").exists()
        assert (out / "robots.txt").exists()
        home_html = (out / "README.md.html").read_text(encoding="utf-8")
        folder_html = (out / "Folder" / "index.html").read_text(encoding="utf-8")
        folder_note_html = (out / "Folder" / "B.md.html").read_text(encoding="utf-8")
        assert 'class="topbar-context topbar-context-note"' in home_html
        assert 'data-current-heading' in home_html
        assert 'data-nav-tree-action="expand"' in home_html
        assert 'data-nav-tree-action="collapse"' in home_html
        assert 'title="Expand all"' in home_html
        assert 'title="Collapse all"' in home_html
        assert 'href="/A.md.html"' in home_html
        assert 'class="sidebar-title">Directory<' in folder_html
        assert 'class="directory-context-nav"' in folder_html
        assert 'href="/A.md.html"' in folder_html
        assert 'href="/README.md.html"' in folder_html
        assert "Same Directory" in folder_html
        assert 'class="directory-list"' in folder_html
        assert 'class="directory-list-item is-file"' in folder_html
        assert 'directory-list-title">B.md<' in folder_html
        assert 'directory-list-preview"># Note B' in folder_html
        assert "This is note B in a folder." in folder_html
        assert 'directory-list-meta">Folder/B.md<' not in folder_html
        assert 'href="/Folder/index.html" class="topbar-breadcrumb-link topbar-breadcrumb-segment"' in folder_note_html
        assert 'href="/Folder/B.md.html" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in folder_note_html


def test_build_static_site_ignores_permalink_and_alias_routes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "README.md").write_text(
        "---\npermalink: about\naliases:\n  - Old Home\n---\n# Home\n",
        encoding="utf-8",
    )
    config = PublisherConfig(vault_path=vault, site_url="https://notes.example.com")
    builder = StaticSiteBuilder(config)
    out = tmp_path / "public"

    builder.build(out, clean=True)

    canonical = (out / "README.md.html").read_text(encoding="utf-8")
    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")

    assert "<h1" in canonical
    assert not (out / "about").exists()
    assert not (out / "Old Home").exists()
    assert "https://notes.example.com/README.md.html" in sitemap


def test_build_static_site_renders_topbar_code_tools_for_text_pages(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "README.md").write_text("# README\n", encoding="utf-8")
    tools_dir = vault / "tools"
    tools_dir.mkdir()
    (tools_dir / "example.py").write_text("print('hello')\n", encoding="utf-8")

    config = PublisherConfig(vault_path=vault, force_include_regexes=(r".*\.py$",))
    builder = StaticSiteBuilder(config)
    out = tmp_path / "public"

    builder.build(out, clean=True)

    code_html = (out / "tools" / "example.py.html").read_text(encoding="utf-8")
    assert 'class="topbar-context topbar-context-code"' in code_html
    assert 'href="/tools/index.html" class="topbar-breadcrumb-link topbar-breadcrumb-segment"' in code_html
    assert 'href="/tools/example.py.html" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in code_html
    assert 'data-code-action="copy-path"' in code_html
    assert 'data-code-action="toggle-wrap"' in code_html
    assert "tools/example.py" in code_html


def test_build_static_site_keeps_canonical_local_resource_urls(vault_local_resources) -> None:
    config = PublisherConfig(
        vault_path=vault_local_resources,
        force_include_regexes=(r".*\.py$",),
    )
    builder = StaticSiteBuilder(config)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "public"
        result = builder.build(out, clean=True)

        note_html = (out / "subdir" / "README.md.html").read_text(encoding="utf-8")
        assert result.attachments_copied >= 3
        assert 'src="/assets/subdir/image.png"' in note_html
        assert 'href="/assets/subdir/doc.pdf"' in note_html
        assert '<a href="/assets/subdir/archive.pin.gz" download="archive.pin.gz">Archive Download</a>' in note_html
        assert 'href="/subdir/tool.py.html"' in note_html
        assert 'href="/subdir/Other.md.html"' in note_html
        assert (out / "assets" / "subdir" / "image.png").exists()
        assert (out / "assets" / "subdir" / "doc.pdf").exists()
        assert (out / "assets" / "subdir" / "archive.pin.gz").exists()


def test_build_static_site_copies_dynamic_obsidian_referenced_text_file(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "attachments").mkdir()
    (vault / "general").mkdir()
    (vault / "attachments" / "config.toml").write_text('name = "vaultpub"\n', encoding="utf-8")
    (vault / "general" / "README.md").write_text("![[../attachments/config.toml]]\n", encoding="utf-8")

    config = PublisherConfig(vault_path=vault)
    builder = StaticSiteBuilder(config)
    out = tmp_path / "public"

    result = builder.build(out, clean=True)

    note_html = (out / "general" / "README.md.html").read_text(encoding="utf-8")
    assert result.attachments_copied >= 1
    assert 'data-embed-source="/assets/attachments/config.toml"' in note_html
    assert (out / "assets" / "attachments" / "config.toml").exists()
