"""Frontmatter / YAML properties parsing."""
from __future__ import annotations

from typing import Any


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str, int]:
    """Extract YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_text, body_start_line).
    body_start_line is the 0-indexed line where body begins.
    """
    if not content.startswith("---"):
        return {}, content, 0

    lines = content.split("\n")
    if len(lines) < 2 or lines[0].strip() != "---":
        return {}, content, 0

    end_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, content, 0

    import yaml

    try:
        fm_text = "\n".join(lines[1:end_idx])
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}

    body = "\n".join(lines[end_idx + 1:])
    return fm, body, end_idx + 1
