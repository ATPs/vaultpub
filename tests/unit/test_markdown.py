"""Tests for markdown rendering."""
from __future__ import annotations

from vaultpub.core.parser.markdown import render_markdown


def test_render_basic_markdown() -> None:
    html = render_markdown("# Hello\n\nWorld")
    assert "<h1" in html
    assert "Hello" in html
    assert "<p>World</p>" in html


def test_render_links() -> None:
    html = render_markdown("[text](https://example.com)")
    assert 'href="https://example.com"' in html
    assert "text" in html


def test_render_code_block() -> None:
    html = render_markdown("```python\nprint('hello')\n```")
    assert "<code" in html
    assert "print" in html


def test_render_html_safe_mode() -> None:
    html = render_markdown("<script>alert('xss')</script>", html_safe_mode=True)
    # In safe mode, raw HTML should be escaped (markdown-it commonmark strips it)
    assert "alert" not in html.lower() or "&lt;script" in html
