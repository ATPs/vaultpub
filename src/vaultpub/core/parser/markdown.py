"""Markdown rendering pipeline."""
from __future__ import annotations

import re
from collections.abc import Sequence

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict
from mdit_py_plugins.tasklists import tasklists_plugin

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TASK_CHECKBOX_RE = re.compile(
    r'^<input class="task-list-item-checkbox"\s+(?:checked="checked"\s+)?type="checkbox">$'
)


def _render_html_token(
    renderer: object,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Remove comments while retaining the configured raw-HTML safety boundary."""
    content = _HTML_COMMENT_RE.sub("", tokens[idx].content)
    return escapeHtml(content) if options["vaultpub_escape_raw_html"] else content


def _render_task_checkbox(
    renderer: object,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render checkboxes emitted by the task-list plugin before sanitization."""
    return tokens[idx].content


def _mark_task_checkboxes(state: StateCore) -> None:
    """Allow only task-list-shaped checkbox tokens through safe HTML rendering."""
    for token in state.tokens:
        if token.type != "inline" or token.children is None:
            continue
        for child in token.children:
            if child.type == "html_inline" and _TASK_CHECKBOX_RE.fullmatch(child.content):
                child.type = "vaultpub_task_checkbox"


def create_markdown_parser(
    strict_line_breaks: bool = False,
    html_safe_mode: bool = True,
) -> MarkdownIt:
    """Create a configured markdown-it-py instance."""
    # Parse HTML in both modes so standard comments can be removed. Safe mode
    # still escapes every non-comment raw HTML token below.
    md = MarkdownIt("commonmark", {"breaks": not strict_line_breaks, "html": True})

    md.options["typographer"] = True
    md.options["vaultpub_escape_raw_html"] = html_safe_mode

    # Enable basic plugins
    md.enable(["table", "strikethrough", "linkify", "smartquotes"])
    md.use(tasklists_plugin, enabled=True)
    md.core.ruler.after("github-tasklists", "vaultpub-task-checkboxes", _mark_task_checkboxes)
    md.add_render_rule("html_block", _render_html_token)
    md.add_render_rule("html_inline", _render_html_token)
    md.add_render_rule("vaultpub_task_checkbox", _render_task_checkbox)

    return md


def render_markdown(
    content: str,
    strict_line_breaks: bool = False,
    html_safe_mode: bool = True,
) -> str:
    """Render markdown content to HTML."""
    md = create_markdown_parser(strict_line_breaks, html_safe_mode)
    return md.render(content)


def render_inline_markdown(
    content: str,
    strict_line_breaks: bool = False,
    html_safe_mode: bool = True,
) -> str:
    """Render Markdown intended for an inline context, such as a callout title."""
    md = create_markdown_parser(strict_line_breaks, html_safe_mode)
    return md.renderInline(content)
