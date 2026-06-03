"""Obsidian comment stripping."""
from __future__ import annotations

import re

_COMMENT_RE = re.compile(r"%%.*?%%", re.DOTALL)


def strip_comments(content: str) -> str:
    """Remove Obsidian %% comments %% from content."""
    return _COMMENT_RE.sub("", content)
