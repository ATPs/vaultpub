"""Tests for HTML sanitization."""
from __future__ import annotations

from vaultpub.core.render.sanitize import add_external_link_attrs, sanitize_html


def test_sanitize_allows_safe_tags() -> None:
    html = "<p>Hello <strong>World</strong></p>"
    result = sanitize_html(html)
    assert "<p>" in result
    assert "<strong>" in result


def test_sanitize_strips_script() -> None:
    html = "<p>Hello</p><script>alert('xss')</script>"
    result = sanitize_html(html)
    assert "<p>Hello</p>" in result
    assert "<script>" not in result
    # bleach strips tags but keeps text content


def test_add_external_link_attrs() -> None:
    html = '<a href="https://example.com">Link</a>'
    result = add_external_link_attrs(html)
    assert 'rel="noopener noreferrer"' in result
    assert 'target="_blank"' in result


def test_add_external_link_attrs_preserves_internal() -> None:
    html = '<a href="/local">Local Link</a>'
    result = add_external_link_attrs(html)
    assert 'target="_blank"' not in result
