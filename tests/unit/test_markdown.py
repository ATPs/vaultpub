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


def test_render_html_comments_are_hidden_but_code_examples_remain() -> None:
    html = render_markdown(
        "Visible <!-- inline comment --> text\n\n"
        "<!-- block comment -->\n\n"
        "`<!-- inline code -->`\n\n"
        "```html\n<!-- fenced code -->\n```\n"
    )

    assert "inline comment" not in html
    assert "block comment" not in html
    assert "&lt;!-- inline code --&gt;" in html
    assert "&lt;!-- fenced code --&gt;" in html


def test_render_task_lists_as_clickable_checkboxes() -> None:
    html = render_markdown("- [ ] Open\n- [x] Done\n")

    assert 'class="contains-task-list"' in html
    assert html.count('class="task-list-item-checkbox"') == 2
    assert html.count('type="checkbox"') == 2
    assert 'class="task-list-item enabled"' in html
    assert "disabled" not in html
    assert 'checked="checked"' in html


def test_render_default_preserves_single_line_breaks() -> None:
    assert "<br" in render_markdown("first line\nsecond line")
    assert "<br" not in render_markdown("first line\nsecond line", strict_line_breaks=True)
