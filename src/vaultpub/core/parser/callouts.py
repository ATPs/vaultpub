"""Callout block parsing."""
from __future__ import annotations

import re

_CALLOUT_RE = re.compile(r'^>\s*\[!(\w+)\]\s*([+-])?\s*(.*?)$')
_CALLOUT_CONTENT_RE = re.compile(r"^>(?:\s(.*)|$)")

CALLOUT_TYPES = {
    "note", "abstract", "summary", "tldr", "info", "todo",
    "tip", "hint", "important", "success", "check", "done",
    "question", "help", "faq", "warning", "caution", "attention",
    "failure", "fail", "missing", "danger", "error", "bug",
    "example", "quote", "cite",
}

CALLOUT_ALIASES: dict[str, str] = {
    "summary": "abstract", "tldr": "abstract",
    "hint": "tip", "important": "tip",
    "check": "success", "done": "success",
    "help": "question", "faq": "question",
    "caution": "warning", "attention": "warning",
    "fail": "failure", "missing": "failure",
    "error": "danger",
    "cite": "quote",
}


def parse_callout_block(lines: list[str], start_idx: int) -> tuple[dict, int]:
    """Parse a callout block starting at lines[start_idx].

    Returns (callout_data, next_line_idx).
    callout_data has: type, title, fold_state, content
    """
    match = _CALLOUT_RE.match(lines[start_idx])
    if not match:
        return {}, start_idx + 1

    raw_type = match.group(1).lower()
    fold_marker = match.group(2)  # + or -
    title = match.group(3).strip() or raw_type.capitalize()

    resolved_type = raw_type
    if raw_type in CALLOUT_ALIASES:
        resolved_type = CALLOUT_ALIASES[raw_type]
    if resolved_type not in CALLOUT_TYPES:
        resolved_type = "note"

    fold_state = "open"
    if fold_marker == "+":
        fold_state = "open"
    elif fold_marker == "-":
        fold_state = "closed"

    content_lines: list[str] = []
    i = start_idx + 1
    while i < len(lines):
        cmatch = _CALLOUT_CONTENT_RE.match(lines[i])
        if cmatch:
            content_lines.append(cmatch.group(1) or "")
        else:
            # Empty line within callout?
            if lines[i].strip() == "" and i + 1 < len(lines):
                nmatch = _CALLOUT_CONTENT_RE.match(lines[i + 1])
                if nmatch:
                    content_lines.append("")
                    i += 1
                    continue
            break
        i += 1

    return {
        "type": resolved_type,
        "original_type": raw_type,
        "title": title,
        "fold_state": fold_state,
        "content": "\n".join(content_lines),
    }, i


def render_callout_html(callout: dict) -> str:
    """Render a parsed callout to HTML."""
    t = callout["type"]
    fold = callout["fold_state"]
    title = callout["title"]
    content = callout["content"]

    icon_map: dict[str, str] = {
        "note": "✎", "abstract": "□", "info": "ℹ", "todo": "☐",
        "tip": "🔥", "success": "✔", "question": "❓",
        "warning": "⚠", "failure": "✘", "danger": "⚡",
        "bug": "🐛", "example": "●", "quote": "❝",
    }
    icon = icon_map.get(t, "✎")

    return f"""\
<div class="callout" data-callout="{t}" data-callout-fold="{fold}">
  <div class="callout-title">
    <span class="callout-icon">{icon}</span>
    <span class="callout-title-inner">{title}</span>
  </div>
  <div class="callout-content">{content}</div>
</div>"""
