"""Obsidian wikilink and embed parser."""
from __future__ import annotations

import re
from collections.abc import Iterator

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
WIKILINK_EMBED_RE = re.compile(r"!\[\[([^\[\]]+?)\]\]")

_FENCE_START_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})")
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_COMMENT_RE = re.compile(r"%%.*?%%", re.DOTALL)


def find_wikilinks(content: str) -> Iterator[tuple[int, int, str, bool]]:
    """Yield (start, end, raw_target, is_embed) for each wikilink in content.

    Skips wikilinks inside code fences, inline code, and Obsidian comments.
    """
    # Mask protected regions
    protected = find_protected_regions(content)

    for match in WIKILINK_EMBED_RE.finditer(content):
        if _in_protected(match.start(), protected):
            continue
        yield match.start(), match.end(), match.group(1), True

    for match in WIKILINK_RE.finditer(content):
        # Skip if preceded by ! (embed already handled above)
        if match.start() > 0 and content[match.start() - 1] == "!":
            continue
        if _in_protected(match.start(), protected):
            continue
        yield match.start(), match.end(), match.group(1), False


def parse_wikilink_target(raw: str) -> tuple[str, str | None, str | None, str | None]:
    """Parse a wikilink target into (target_path, anchor, display_text, size).

    Examples:
        [[Note]] -> ("Note", None, None, None)
        [[Note|Display]] -> ("Note", None, "Display", None)
        [[Note#Heading]] -> ("Note", "Heading", None, None)
        [[Note#Heading|Display]] -> ("Note", "Heading", "Display", None)
        [[image.png|300]] -> ("image.png", None, None, "300")
        [[image.png|300x200]] -> ("image.png", None, None, "300x200")
        [[#Heading]] -> ("", "Heading", None, None)
        [[^block-id]] -> ("", "^block-id", None, None)
    """
    anchor: str | None = None
    display_text: str | None = None
    size: str | None = None
    target = raw

    # Handle display text or size after |
    if "|" in target:
        parts = target.split("|", 1)
        target = parts[0]
        after = parts[1]
        if re.match(r"^\d+(?:x\d+)?$", after):
            size = after
        else:
            display_text = after

    # Handle anchor
    if "#" in target:
        target, anchor = target.split("#", 1)
        if not target:
            target = ""

    return target, anchor, display_text, size


def find_inline_tags(content: str, protected: list[tuple[int, int]] | None = None) -> Iterator[tuple[str, int]]:
    """Yield (tag_name, position) for inline #tags in content.

    Avoids code fences, inline code, comments, and URL fragments.
    """
    if protected is None:
        protected = find_protected_regions(content)

    for match in re.finditer(r"(?<!\w)(?<!/)(?<!\[)#([a-zA-Z一-鿿぀-ゟ゠-ヿ가-힯][\w一-鿿぀-ゟ゠-ヿ가-힯/_-]*)", content):
        if _in_protected(match.start(), protected):
            continue
        yield match.group(1), match.start()


def find_markdown_links(
    content: str, protected: list[tuple[int, int]] | None = None
) -> Iterator[tuple[str, str | None, str, bool]]:
    """Yield (url, display, raw_match, is_embed) for markdown [text](url) links."""
    if protected is None:
        protected = find_protected_regions(content)

    for match in re.finditer(r"!?\[([^\]]*)\]\(([^)]+)\)", content):
        if _in_protected(match.start(), protected):
            continue
        is_embed = match.group(0).startswith("!")
        yield match.group(2), match.group(1), match.group(0), is_embed


def strip_obsidian_comments(content: str) -> str:
    """Remove Obsidian %% comments %% from content."""
    return _COMMENT_RE.sub("", content)


def find_heading_blocks(content: str) -> Iterator[tuple[int, int, str, str]]:
    """Yield (start_line, end_line, heading_slug, block_id) for ^block-id patterns."""
    for match in re.finditer(r"\^([a-zA-Z0-9_-]+)", content):
        line_num = content[:match.start()].count("\n")
        yield line_num, line_num + 1, "", match.group(1)


def find_protected_regions(content: str) -> list[tuple[int, int]]:
    """Find regions protected from wikilink parsing: code fences and inline code."""
    regions: list[tuple[int, int]] = []

    # Inline code
    for match in _CODE_SPAN_RE.finditer(content):
        regions.append((match.start(), match.end()))

    # Code fences
    lines = content.split("\n")
    in_fence = False
    fence_start = 0

    for i, line in enumerate(lines):
        m = _FENCE_START_RE.match(line)
        if m:
            pos = sum(len(line) + 1 for line in lines[:i])
            if not in_fence:
                in_fence = True
                fence_start = pos
            else:
                in_fence = False
                regions.append((fence_start, pos + len(line)))

    # Obsidian comments
    for match in _COMMENT_RE.finditer(content):
        regions.append((match.start(), match.end()))

    return sorted(regions)


def _in_protected(pos: int, protected: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in protected)
