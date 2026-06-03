"""Tests for wikilink and Obsidian link parsing."""
from __future__ import annotations

from vaultpub.core.parser.obsidian_links import (
    find_inline_tags,
    find_wikilinks,
    parse_wikilink_target,
    strip_obsidian_comments,
)


def test_parse_simple_wikilink() -> None:
    target, anchor, display, size = parse_wikilink_target("Note")
    assert target == "Note"
    assert anchor is None
    assert display is None


def test_parse_wikilink_with_display() -> None:
    target, anchor, display, size = parse_wikilink_target("Note|Display Text")
    assert target == "Note"
    assert display == "Display Text"


def test_parse_wikilink_with_anchor() -> None:
    target, anchor, display, size = parse_wikilink_target("Note#Heading")
    assert target == "Note"
    assert anchor == "Heading"


def test_parse_wikilink_with_anchor_and_display() -> None:
    target, anchor, display, size = parse_wikilink_target("Note#Heading|Text")
    assert target == "Note"
    assert anchor == "Heading"
    assert display == "Text"


def test_parse_wikilink_block_ref() -> None:
    target, anchor, display, size = parse_wikilink_target("Note#^block-id")
    assert target == "Note"
    assert anchor == "^block-id"


def test_parse_wikilink_current_page() -> None:
    target, anchor, display, size = parse_wikilink_target("#Heading")
    assert target == ""
    assert anchor == "Heading"


def test_parse_wikilink_image_size() -> None:
    target, anchor, display, size = parse_wikilink_target("image.png|300")
    assert target == "image.png"
    assert size == "300"

    target, anchor, display, size = parse_wikilink_target("image.png|300x200")
    assert target == "image.png"
    assert size == "300x200"


def test_find_wikilinks() -> None:
    content = "Some text [[Note]] and [[Other|Display]] text."
    links = list(find_wikilinks(content))
    assert len(links) == 2
    assert links[0][2] == "Note"
    assert not links[0][3]  # not embed
    assert links[1][2] == "Other|Display"


def test_find_embed_wikilinks() -> None:
    content = "Here is ![[image.png]] and [[normal]]."
    links = list(find_wikilinks(content))
    assert len(links) == 2
    embeds = [link for link in links if link[3]]
    non_embeds = [link for link in links if not link[3]]
    assert len(embeds) == 1
    assert len(non_embeds) == 1
    assert embeds[0][2] == "image.png"
    assert non_embeds[0][2] == "normal"


def test_find_wikilinks_skip_code_blocks() -> None:
    content = "[[outside]]\n\n```\n[[inside]]\n```\n\n[[also outside]]"
    links = list(find_wikilinks(content))
    targets = [link[2] for link in links]
    assert "outside" in targets
    assert "inside" not in targets
    assert "also outside" in targets


def test_strip_comments() -> None:
    content = "Visible %% hidden %% more visible"
    result = strip_obsidian_comments(content)
    assert "Visible " in result
    assert "hidden" not in result
    assert "more visible" in result


def test_find_inline_tags() -> None:
    content = "Some text #tag1 and #tag2/subtag and not #123."
    tags = list(find_inline_tags(content))
    tag_names = [t[0] for t in tags]
    assert "tag1" in tag_names
    assert "tag2/subtag" in tag_names
