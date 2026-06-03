"""Tests for frontmatter parsing."""
from __future__ import annotations

from vaultpub.core.frontmatter import parse_frontmatter


def test_parse_frontmatter_basic() -> None:
    content = """\
---
title: My Title
tags:
  - demo
  - test
---

# Body starts here

Some content.
"""
    fm, body, body_start = parse_frontmatter(content)
    assert fm["title"] == "My Title"
    assert fm["tags"] == ["demo", "test"]
    assert "# Body starts here" in body
    assert body_start == 6


def test_parse_no_frontmatter() -> None:
    content = "# Just a heading\n\nSome text."
    fm, body, body_start = parse_frontmatter(content)
    assert fm == {}
    assert body == content
    assert body_start == 0


def test_parse_empty_frontmatter() -> None:
    content = """\
---
---

Body only.
"""
    fm, body, body_start = parse_frontmatter(content)
    assert fm == {}
    assert "Body only." in body
