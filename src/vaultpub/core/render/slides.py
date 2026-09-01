"""Slide segmentation and safe Reveal configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from vaultpub.core.frontmatter import parse_frontmatter
from vaultpub.core.models import NavNode, NoteRecord, VaultIndex
from vaultpub.core.parser.markdown import create_markdown_parser
from vaultpub.core.parser.obsidian_links import strip_obsidian_comments

SlideSplitMode = Literal["explicit", "headings", "single"]

REVEAL_THEMES = frozenset(
    {
        "beige",
        "black",
        "black-contrast",
        "blood",
        "dracula",
        "league",
        "moon",
        "night",
        "serif",
        "simple",
        "sky",
        "solarized",
        "white",
        "white-contrast",
    }
)
REVEAL_TRANSITIONS = frozenset({"none", "fade", "slide", "convex", "concave", "zoom"})


@dataclass(frozen=True)
class SlideOptions:
    """Validated, serializable Reveal configuration for one note deck."""

    theme: str = "white"
    transition: str = "slide"
    controls: bool = True
    progress: bool = True
    slide_number: bool = True
    center: bool = True
    width: int = 1600
    height: int = 900
    hash: bool = True

    def reveal_config(self) -> dict[str, bool | int | str]:
        return {
            "transition": self.transition,
            "controls": self.controls,
            "progress": self.progress,
            "slideNumber": self.slide_number,
            "center": self.center,
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
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


def segment_slides(raw_markdown: str) -> SegmentedSlides:
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
    if separator_lines:
        return SegmentedSlides("explicit", tuple(_split_at_lines(lines, separator_lines)))

    h2_lines = sorted(
        {
            token.map[0]
            for token in tokens
            if token.type == "heading_open" and token.tag == "h2" and token.map is not None
        }
    )
    if h2_lines:
        return SegmentedSlides("headings", tuple(_split_at_lines(lines, h2_lines, keep_first=True)))

    return SegmentedSlides("single", (body,))


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

    return SlideOptions(
        theme=theme if isinstance(theme, str) and theme in REVEAL_THEMES else defaults.theme,
        transition=(
            transition if isinstance(transition, str) and transition in REVEAL_TRANSITIONS else defaults.transition
        ),
        controls=_bool_or_default(raw.get("controls"), defaults.controls),
        progress=_bool_or_default(raw.get("progress"), defaults.progress),
        slide_number=_bool_or_default(raw.get("slideNumber"), defaults.slide_number),
        center=_bool_or_default(raw.get("center"), defaults.center),
        width=_positive_int_or_default(width, defaults.width),
        height=_positive_int_or_default(height, defaults.height),
        hash=_bool_or_default(raw.get("hash"), defaults.hash),
    )


def collect_directory_notes(directory: NavNode, index: VaultIndex) -> list[NoteRecord]:
    """Return visible descendant notes in the scanner's established navigation order."""
    notes: list[NoteRecord] = []

    def _visit(node: NavNode) -> None:
        for child in node.children:
            if child.nav_hidden:
                continue
            if child.is_dir:
                _visit(child)
                continue
            note_id = index.notes_by_path.get(child.path)
            if note_id is not None:
                notes.append(index.notes_by_id[note_id])

    _visit(directory)
    return notes


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
