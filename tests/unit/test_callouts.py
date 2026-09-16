"""Tests for callout parsing."""
from __future__ import annotations

from vaultpub.core.parser.callouts import parse_callout_block, render_callout_html


def test_parse_note_callout() -> None:
    lines = [
        "> [!note] Simple note",
        "> This is a note callout.",
        "> Second line.",
        "",
        "After callout.",
    ]
    callout, next_idx = parse_callout_block(lines, 0)
    assert callout["type"] == "note"
    assert callout["title"] == "Simple note"
    assert "This is a note callout" in callout["content"]
    assert next_idx == 3


def test_parse_foldable_callout() -> None:
    lines = [
        "> [!tip]+ Expanded tip",
        "> Content here.",
        "",
    ]
    callout, next_idx = parse_callout_block(lines, 0)
    assert callout["type"] == "tip"
    assert callout["fold_state"] == "open"


def test_parse_collapsed_callout() -> None:
    lines = [
        "> [!warning]- Collapsed",
        "> Hidden content.",
    ]
    callout, next_idx = parse_callout_block(lines, 0)
    assert callout["fold_state"] == "closed"


def test_parse_unknown_type_defaults_to_note() -> None:
    lines = [
        "> [!custom] Something",
        "> Content.",
    ]
    callout, next_idx = parse_callout_block(lines, 0)
    assert callout["type"] == "note"


def test_render_callout_html() -> None:
    callout = {
        "type": "tip",
        "fold_state": "open",
        "title": "Pro Tip",
        "content": "This is a tip.",
    }
    html = render_callout_html(callout)
    assert 'data-callout="tip"' in html
    assert 'data-callout-fold="open"' in html
    assert "Pro Tip" in html
    assert "This is a tip." in html


def test_render_callout_html_uses_pre_rendered_title_and_content() -> None:
    callout = {
        "type": "info",
        "fold_state": "open",
        "title": "Scope",
        "content": "Audience",
    }

    html = render_callout_html(
        callout,
        title_html="<strong>Scope</strong>",
        content_html="<ul><li>Audience</li></ul>",
    )

    assert '<span class="callout-title-inner"><strong>Scope</strong></span>' in html
    assert '<div class="callout-content"><ul><li>Audience</li></ul></div>' in html
