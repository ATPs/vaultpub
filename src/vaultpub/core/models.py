from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Literal


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    slug: str
    line: int


@dataclass(frozen=True)
class BlockRef:
    block_id: str
    line_start: int
    line_end: int
    raw: str


@dataclass
class InternalLink:
    raw: str
    source_id: str
    target_text: str
    target_id: str | None = None
    anchor: str | None = None
    display_text: str | None = None
    is_embed: bool = False
    is_attachment: bool = False
    is_resolved: bool = False
    reason_unresolved: str | None = None


@dataclass
class NoteRecord:
    id: str
    rel_path: PurePosixPath
    url_path: str
    title: str
    stem: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    raw_markdown: str = ""
    plain_text: str = ""
    excerpt: str = ""
    headings: list[Heading] = field(default_factory=list)
    blocks: dict[str, BlockRef] = field(default_factory=dict)
    outgoing_links: list[InternalLink] = field(default_factory=list)
    embedded_refs: list[InternalLink] = field(default_factory=list)
    backlinks: set[str] = field(default_factory=set)
    ctime_ns: int = 0
    mtime_ns: int = 0
    size: int = 0
    content_hash: str = ""


@dataclass
class TextPageRecord:
    id: str
    rel_path: PurePosixPath
    url_path: str
    title: str
    stem: str
    language: str
    raw_text: str
    plain_text: str
    excerpt: str
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass
class AttachmentRecord:
    id: str
    rel_path: PurePosixPath
    url_path: str
    mime_type: str
    size: int
    mtime_ns: int


@dataclass
class NavNode:
    label: str
    path: str
    url: str
    is_dir: bool = False
    children: list[NavNode] = field(default_factory=list)


@dataclass
class GraphNode:
    id: str
    label: str
    title: str
    url: str | None = None
    group: Literal["note", "tag", "attachment"] = "note"
    value: int = 1


@dataclass
class GraphEdge:
    source: str
    target: str
    kind: Literal["link", "embed", "tag", "attachment"] = "link"


@dataclass
class GraphData:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


@dataclass
class VaultIndex:
    notes_by_id: dict[str, NoteRecord] = field(default_factory=dict)
    notes_by_path: dict[str, str] = field(default_factory=dict)
    notes_by_stem: dict[str, list[str]] = field(default_factory=dict)
    notes_by_alias: dict[str, list[str]] = field(default_factory=dict)
    attachments_by_path: dict[str, AttachmentRecord] = field(default_factory=dict)
    text_pages_by_path: dict[str, TextPageRecord] = field(default_factory=dict)
    text_pages_by_id: dict[str, TextPageRecord] = field(default_factory=dict)
    nav_tree: NavNode | None = None
    tags: dict[str, set[str]] = field(default_factory=dict)
    graph: GraphData = field(default_factory=GraphData)
    search_documents: list[dict[str, object]] = field(default_factory=list)
    permalinks: dict[str, str] = field(default_factory=dict)
    redirects: dict[str, str] = field(default_factory=dict)
