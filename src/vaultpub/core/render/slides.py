"""Slide segmentation, fingerprints, and safe Reveal configuration helpers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Literal

from vaultpub.core.frontmatter import parse_frontmatter
from vaultpub.core.models import NavNode, NoteRecord, VaultIndex
from vaultpub.core.parser.markdown import create_markdown_parser
from vaultpub.core.parser.obsidian_links import strip_obsidian_comments

SlideSplitMode = Literal["explicit", "headings", "single"]
SlideSplitPolicy = Literal[
    "auto", "chapters", "sections", "detail", "fit", "explicit", "single", "h1", "h2", "h3"
]
SlideDeckOrder = Literal[
    "predefined", "name-asc", "name-desc", "created-desc", "created-asc", "modified-desc", "modified-asc"
]

SLIDE_SPLIT_POLICIES = frozenset(
    {"auto", "chapters", "sections", "detail", "fit", "explicit", "single", "h1", "h2", "h3"}
)
SLIDE_DECK_ORDERS = frozenset(
    {"predefined", "name-asc", "name-desc", "created-desc", "created-asc", "modified-desc", "modified-asc"}
)

READING_THEMES = frozenset(
    {
        "light",
        "dark",
        "nord",
        "solarized",
        "dracula",
        "forest",
        "glass-light",
        "glass-dark",
        "obsidian",
        "catppuccin",
        "colorful",
        "colorful-dark",
    }
)
REVEAL_TRANSITIONS = frozenset({"none", "fade", "slide", "convex", "concave", "zoom"})


@dataclass(frozen=True)
class SlideOptions:
    """Validated, serializable Reveal configuration for one note deck."""

    theme: str = "light"
    transition: str = "slide"
    controls: bool = False
    progress: bool = True
    slide_number: bool = True
    center: bool = True
    width: int = 1600
    height: int = 900
    hash: bool = True
    split: SlideSplitPolicy = "auto"
    code_wrap: bool = True

    def reveal_config(self) -> dict[str, bool | int | str]:
        return {
            "transition": self.transition,
            "controls": False,
            "progress": self.progress,
            "slideNumber": self.slide_number,
            "center": self.center,
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
        }

    def client_config(self, split_override: SlideSplitPolicy | None = None) -> dict[str, bool | int | str]:
        """Return safe deck defaults consumed by the presentation controls."""
        return {
            "theme": self.theme,
            "transition": self.transition,
            "progress": self.progress,
            "slideNumber": self.slide_number,
            "center": self.center,
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
            "codeWrap": self.code_wrap,
            "split": split_override or self.split,
        }


@dataclass(frozen=True)
class SegmentedSlides:
    mode: SlideSplitMode
    fragments: tuple[str, ...]


@dataclass(frozen=True)
class RenderedSlide:
    html: str
    source_note_id: str
    source_path: str
    index: int
    mode: SlideSplitMode


@dataclass(frozen=True)
class SlideFragmentDescriptor:
    """Lightweight navigation metadata for one unrendered slide fragment."""

    index: int
    title: str


@dataclass(frozen=True)
class SlideNoteDescriptor:
    """One source note in a lazily hydrated multi-note deck."""

    id: str
    title: str
    source_path: str
    fragments: tuple[SlideFragmentDescriptor, ...]
    fingerprint: str = ""


def segment_slides(raw_markdown: str, split: SlideSplitPolicy = "auto") -> SegmentedSlides:
    """Split one source note into presentation fragments without changing its content."""
    _frontmatter, body, _body_start = parse_frontmatter(raw_markdown)
    body = strip_obsidian_comments(body)
    lines = body.splitlines(keepends=True)
    tokens = create_markdown_parser().parse(body)

    separator_lines = sorted(
        {
            token.map[0]
            for token in tokens
            if token.type == "hr"
            and token.map is not None
            and 0 <= token.map[0] < len(lines)
            and lines[token.map[0]].strip() == "---"
        }
    )
    normalized_split = {"h1": "chapters", "h2": "sections", "h3": "detail"}.get(split, split)
    if normalized_split in ("auto", "chapters", "sections", "detail", "fit", "explicit") and separator_lines:
        return SegmentedSlides("explicit", tuple(_split_at_lines(lines, separator_lines)))

    if normalized_split in ("explicit", "single"):
        return SegmentedSlides("single", (body,))

    if normalized_split == "fit":
        return SegmentedSlides("single", (body,))

    heading_tags = {
        "auto": {"h2"},
        "chapters": {"h1"},
        "sections": {"h2"},
        "detail": {"h2", "h3"},
    }[normalized_split]
    heading_lines = sorted(
        {
            token.map[0]
            for token in tokens
            if token.type == "heading_open" and token.tag in heading_tags and token.map is not None
        }
    )
    if heading_lines:
        return SegmentedSlides("headings", tuple(_split_at_lines(lines, heading_lines, keep_first=True)))

    return SegmentedSlides("single", (body,))


def describe_slide_note(note: NoteRecord, split_override: SlideSplitPolicy | None = None) -> SlideNoteDescriptor:
    """Return slide labels without converting the note's Markdown into HTML."""
    segmented = segment_slides(note.raw_markdown, split_override or slide_options(note.frontmatter).split)
    fragments = tuple(
        SlideFragmentDescriptor(index=index, title=_fragment_title(fragment, note.title, index))
        for index, fragment in enumerate(segmented.fragments)
    )
    return SlideNoteDescriptor(
        id=note.id,
        title=note.title,
        source_path=note.rel_path.as_posix(),
        fragments=fragments,
        fingerprint=slide_deck_fingerprint(note, split_override),
    )


def slide_embed_requested(value: object) -> bool:
    """Return whether an explicit, opt-in Slide View embed mode was requested."""
    return isinstance(value, str) and value.strip().lower() in {"1", "true"}


def slide_deck_fingerprint(note: NoteRecord, split_override: SlideSplitPolicy | None = None) -> str:
    """Return a stable fingerprint for the segmented source deck.

    The fingerprint deliberately covers source identity, the effective split
    policy, and the exact segmented Markdown. Rendered HTML and presentation
    preferences are not part of the cue-point identity.
    """
    effective_split = split_override or slide_options(note.frontmatter).split
    segmented = segment_slides(note.raw_markdown, effective_split)
    payload = {
        "version": 1,
        "noteId": note.id,
        "sourcePath": note.rel_path.as_posix(),
        "split": effective_split,
        "mode": segmented.mode,
        "fragments": segmented.fragments,
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fragment_title(fragment: str, fallback: str, index: int) -> str:
    tokens = create_markdown_parser().parse(fragment)
    for position, token in enumerate(tokens):
        if token.type != "heading_open" or position + 1 >= len(tokens):
            continue
        inline = tokens[position + 1]
        if inline.type == "inline" and inline.content.strip():
            return inline.content.strip()
    return fallback if index == 0 else f"{fallback} ({index + 1})"


def slide_options(frontmatter: object) -> SlideOptions:
    """Return the allowlisted Reveal configuration declared in note frontmatter."""
    if not isinstance(frontmatter, dict):
        return SlideOptions()
    raw = frontmatter.get("slide")
    if not isinstance(raw, dict):
        return SlideOptions()

    defaults = SlideOptions()
    theme = raw.get("theme")
    transition = raw.get("transition")
    width = raw.get("width")
    height = raw.get("height")
    split = raw.get("split")

    return SlideOptions(
        theme=theme if isinstance(theme, str) and theme in READING_THEMES else defaults.theme,
        transition=(
            transition if isinstance(transition, str) and transition in REVEAL_TRANSITIONS else defaults.transition
        ),
        controls=False,
        progress=_bool_or_default(raw.get("progress"), defaults.progress),
        slide_number=_bool_or_default(raw.get("slideNumber"), defaults.slide_number),
        center=_bool_or_default(raw.get("center"), defaults.center),
        width=_positive_int_or_default(width, defaults.width),
        height=_positive_int_or_default(height, defaults.height),
        hash=_bool_or_default(raw.get("hash"), defaults.hash),
        split=validated_slide_split(split) or defaults.split,
        code_wrap=_bool_or_default(raw.get("codeWrap"), defaults.code_wrap),
    )


def validated_slide_split(value: object) -> SlideSplitPolicy | None:
    """Return one safe slide split policy, or None for missing/invalid input."""
    return value if isinstance(value, str) and value in SLIDE_SPLIT_POLICIES else None


def slide_split_override(query_value: object, cookie_value: object) -> SlideSplitPolicy | None:
    """Resolve an optional viewer override, preferring a shareable query value."""
    return validated_slide_split(query_value) or validated_slide_split(cookie_value)


def validated_slide_deck_order(value: object) -> SlideDeckOrder | None:
    """Return one supported multi-note deck order, or None for invalid input."""
    return value if isinstance(value, str) and value in SLIDE_DECK_ORDERS else None


def collect_directory_notes(
    directory: NavNode,
    index: VaultIndex,
    order: SlideDeckOrder = "predefined",
) -> list[NoteRecord]:
    """Return visible descendant notes using the matching normal-navigation order."""
    notes: list[NoteRecord] = []

    def _visit(node: NavNode) -> None:
        for child in _ordered_visible_children(node, order):
            if child.is_dir:
                _visit(child)
                continue
            note_id = index.notes_by_path.get(child.path)
            if note_id is not None:
                notes.append(index.notes_by_id[note_id])

    _visit(directory)
    return notes


def collect_slide_scope_directories(directory: NavNode, index: VaultIndex) -> list[NavNode]:
    """Return visible descendant folders that can produce a non-empty note deck."""
    scopes: list[NavNode] = []

    def _visit(node: NavNode) -> None:
        for child in node.children:
            if child.nav_hidden or not child.is_dir:
                continue
            if collect_directory_notes(child, index):
                scopes.append(child)
            _visit(child)

    _visit(directory)
    return scopes


def _ordered_visible_children(node: NavNode, order: SlideDeckOrder) -> list[NavNode]:
    indexed = [(position, child) for position, child in enumerate(node.children) if not child.nav_hidden]
    if len(indexed) < 2:
        return [child for _position, child in indexed]

    has_predefined_order = any(child.predefined_order for _position, child in indexed)

    def _compare(left: tuple[int, NavNode], right: tuple[int, NavNode]) -> int:
        left_position, left_node = left
        right_position, right_node = right
        if left_node.starred != right_node.starred:
            return -1 if left_node.starred else 1
        if left_node.starred:
            return left_position - right_position
        if order == "predefined" or (order == "modified-desc" and has_predefined_order):
            return left_position - right_position
        if left_node.is_dir != right_node.is_dir:
            return -1 if left_node.is_dir else 1
        if order == "name-asc":
            return _compare_navigation_names(left_node, right_node)
        if order == "name-desc":
            return _compare_navigation_names(right_node, left_node)

        timestamp_name = "created_ns" if order.startswith("created") else "modified_ns"
        left_time = int(getattr(left_node, timestamp_name, 0) or 0)
        right_time = int(getattr(right_node, timestamp_name, 0) or 0)
        if left_time != right_time:
            if not left_time:
                return 1
            if not right_time:
                return -1
            return (right_time - left_time) if order.endswith("desc") else (left_time - right_time)
        return _compare_navigation_names(left_node, right_node)

    return [child for _position, child in sorted(indexed, key=cmp_to_key(_compare))]


def _compare_navigation_names(left: NavNode, right: NavNode) -> int:
    left_name = (left.raw_label or left.label).casefold()
    right_name = (right.raw_label or right.label).casefold()
    return (left_name > right_name) - (left_name < right_name)


def _split_at_lines(lines: list[str], boundary_lines: list[int], keep_first: bool = False) -> list[str]:
    starts = [0, *boundary_lines, len(lines)]
    fragments: list[str] = []

    for index, start in enumerate(starts[:-1]):
        end = starts[index + 1]
        if not keep_first and index > 0:
            start += 1
        fragment = _trim_blank_lines("".join(lines[start:end]))
        if fragment:
            fragments.append(fragment)

    return fragments or [""]


def _trim_blank_lines(content: str) -> str:
    lines = content.splitlines(keepends=True)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "".join(lines)


def _bool_or_default(value: object, default: bool) -> bool:
    return value if type(value) is bool else default


def _positive_int_or_default(value: object, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else default
