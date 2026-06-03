"""Markdown rendering pipeline."""
from __future__ import annotations

from markdown_it import MarkdownIt


def create_markdown_parser(
    strict_line_breaks: bool = False,
    html_safe_mode: bool = True,
) -> MarkdownIt:
    """Create a configured markdown-it-py instance."""
    md = MarkdownIt("commonmark", {"breaks": not strict_line_breaks, "html": not html_safe_mode})

    md.options["typographer"] = True

    # Enable basic plugins
    md.enable(["table", "strikethrough", "linkify", "smartquotes"])

    return md


def render_markdown(
    content: str,
    strict_line_breaks: bool = False,
    html_safe_mode: bool = True,
) -> str:
    """Render markdown content to HTML."""
    md = create_markdown_parser(strict_line_breaks, html_safe_mode)
    return md.render(content)
