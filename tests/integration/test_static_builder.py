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
        assert (out / "search-index.json").exists()
        assert (out / "graph.json").exists()
        assert (out / "robots.txt").exists()
        home_html = (out / "README" / "index.html").read_text(encoding="utf-8")
        assert 'class="topbar-context topbar-context-note"' in home_html
        assert 'data-current-heading' in home_html


def test_build_static_site_uses_permalink_as_canonical(tmp_path: Path) -> None:
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

    canonical = (out / "about" / "index.html").read_text(encoding="utf-8")
    default_redirect = (out / "README" / "index.html").read_text(encoding="utf-8")
    alias_redirect = (out / "Old Home" / "index.html").read_text(encoding="utf-8")
    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")

    assert "<h1" in canonical
    assert 'content="0;url=/about"' in default_redirect
    assert 'content="0;url=/about"' in alias_redirect
    assert "https://notes.example.com/about" in sitemap
    assert "https://notes.example.com/README" not in sitemap


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

    code_html = (out / "tools" / "example.py" / "index.html").read_text(encoding="utf-8")
    assert 'class="topbar-context topbar-context-code"' in code_html
    assert 'data-code-action="copy-path"' in code_html
    assert 'data-code-action="toggle-wrap"' in code_html
    assert "tools/example.py" in code_html
