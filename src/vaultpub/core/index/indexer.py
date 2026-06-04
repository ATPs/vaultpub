"""Vault indexer — builds VaultIndex from scanned notes."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import (
    AttachmentRecord,
    GraphData,
    GraphEdge,
    GraphNode,
    Heading,
    InternalLink,
    NoteRecord,
    TextPageRecord,
    VaultIndex,
)
from vaultpub.core.parser.obsidian_links import (
    find_wikilinks,
    parse_wikilink_target,
    strip_obsidian_comments,
)
from vaultpub.core.scanner import VaultScanner


class VaultIndexer:
    """Builds a complete VaultIndex from a vault."""

    def __init__(self, config: PublisherConfig) -> None:
        self.config = config
        self.scanner = VaultScanner(config)

    def build(self) -> VaultIndex:
        notes, attachments, text_pages, nav_tree = self.scanner.scan()

        for note in notes:
            self._parse_note_body(note)

        notes_by_id: dict[str, NoteRecord] = {n.id: n for n in notes}
        notes_by_path: dict[str, str] = {}
        notes_by_stem: dict[str, list[str]] = {}
        notes_by_alias: dict[str, list[str]] = {}
        attachments_by_path: dict[str, AttachmentRecord] = {a.rel_path.as_posix(): a for a in attachments}
        text_pages_by_path: dict[str, TextPageRecord] = {t.rel_path.as_posix(): t for t in text_pages}
        text_pages_by_id: dict[str, TextPageRecord] = {t.id: t for t in text_pages}

        for note in notes:
            notes_by_path[note.rel_path.as_posix()] = note.id
            notes_by_stem.setdefault(note.stem, []).append(note.id)
            for alias in note.aliases:
                notes_by_alias.setdefault(alias.lower(), []).append(note.id)

        for note in notes:
            self._resolve_links(note, notes_by_id, notes_by_path, notes_by_stem, notes_by_alias, attachments_by_path)

        for note in notes:
            for link in note.outgoing_links:
                if link.is_resolved and link.target_id and not link.is_embed:
                    target = notes_by_id.get(link.target_id)
                    if target:
                        target.backlinks.add(note.id)

        graph = self._build_graph(notes)
        search_docs = self._build_search_documents(notes, text_pages)

        tags: dict[str, set[str]] = {}
        for note in notes:
            for tag in note.tags:
                key = tag.lower()
                tags.setdefault(key, set()).add(note.id)

        permalinks: dict[str, str] = {}
        redirects: dict[str, str] = {}
        for note in notes:
            permalink = note.frontmatter.get("permalink")
            if permalink:
                p = "/" + str(permalink).lstrip("/")
                permalinks[p] = note.id
                redirects[note.url_path] = p

        return VaultIndex(
            notes_by_id=notes_by_id,
            notes_by_path=notes_by_path,
            notes_by_stem=notes_by_stem,
            notes_by_alias=notes_by_alias,
            attachments_by_path=attachments_by_path,
            text_pages_by_path=text_pages_by_path,
            text_pages_by_id=text_pages_by_id,
            nav_tree=nav_tree,
            tags=tags,
            graph=graph,
            search_documents=search_docs,
            permalinks=permalinks,
            redirects=redirects,
        )

    def _parse_note_body(self, note: NoteRecord) -> None:
        content = note.raw_markdown
        visible = strip_obsidian_comments(content)

        for match in re.finditer(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", visible, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            slug = _slugify(text)
            line = visible[:match.start()].count("\n")
            note.headings.append(Heading(level=level, text=text, slug=slug, line=line))

        for match in re.finditer(r"\^([a-zA-Z0-9_-]+)", visible):
            block_id = match.group(1)
            note.blocks[block_id] = None  # type: ignore[assignment]

        # Merge inline tags
        from vaultpub.core.parser.obsidian_links import find_inline_tags

        for tag_name, _pos in find_inline_tags(visible):
            note.tags.add(tag_name)

        for _start, _end, raw_target, is_embed in find_wikilinks(visible):
            target_text, anchor, display_text, size = parse_wikilink_target(raw_target)
            link = InternalLink(
                raw=f"[[{raw_target}]]",
                source_id=note.id,
                target_text=target_text,
                anchor=anchor,
                display_text=display_text,
                is_embed=is_embed,
                is_attachment=any(
                    target_text.lower().endswith(f".{ext}")
                    for ext in self.config.allowed_attachment_types
                ),
            )
            if is_embed:
                note.embedded_refs.append(link)
            else:
                note.outgoing_links.append(link)

    def _resolve_links(
        self,
        note: NoteRecord,
        notes_by_id: dict[str, NoteRecord],
        notes_by_path: dict[str, str],
        notes_by_stem: dict[str, list[str]],
        notes_by_alias: dict[str, list[str]],
        attachments_by_path: dict[str, AttachmentRecord],
    ) -> None:
        for link in list(note.outgoing_links) + list(note.embedded_refs):
            target = link.target_text

            if target == "":
                link.is_resolved = True
                link.target_id = note.id
                continue

            if target.startswith(("http://", "https://", "//")):
                link.is_resolved = True
                continue

            if link.is_attachment:
                att_path = target
                if att_path in attachments_by_path:
                    link.is_resolved = True
                    link.target_id = att_path
                    continue
                note_dir = note.rel_path.parent
                att_path = (note_dir / target).as_posix()
                if att_path in attachments_by_path:
                    link.is_resolved = True
                    link.target_id = att_path
                    continue

            target_clean = target
            if not target_clean.endswith(".md"):
                target_clean += ".md"
            if target_clean in notes_by_path:
                link.is_resolved = True
                link.target_id = notes_by_path[target_clean]
                continue
            if target in notes_by_path:
                link.is_resolved = True
                link.target_id = notes_by_path[target]
                continue

            note_dir = note.rel_path.parent
            rel_target = (note_dir / target).as_posix()
            if rel_target in notes_by_path:
                link.is_resolved = True
                link.target_id = notes_by_path[rel_target]
                continue
            rel_target_md = rel_target + ".md"
            if rel_target_md in notes_by_path:
                link.is_resolved = True
                link.target_id = notes_by_path[rel_target_md]
                continue

            stem = PurePosixPath(target).stem
            if stem in notes_by_stem:
                candidates = notes_by_stem[stem]
                same_dir = [c for c in candidates if notes_by_id[c].rel_path.parent == note.rel_path.parent]
                if same_dir:
                    link.is_resolved = True
                    link.target_id = same_dir[0]
                    if len(same_dir) > 1:
                        link.reason_unresolved = f"Ambiguous: {len(same_dir)} matches in directory"
                    continue
                link.is_resolved = True
                link.target_id = candidates[0]
                if len(candidates) > 1:
                    link.reason_unresolved = f"Ambiguous: {len(candidates)} matches"
                continue

            alias_key = target.lower()
            if alias_key in notes_by_alias:
                link.is_resolved = True
                link.target_id = notes_by_alias[alias_key][0]
                continue

            link.reason_unresolved = "Target not found"

    def _build_graph(self, notes: list[NoteRecord]) -> GraphData:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()
        seen_tags: set[str] = set()

        for note in notes:
            nid = f"note:{note.id}"
            if nid not in seen_nodes:
                seen_nodes.add(nid)
                nodes.append(
                    GraphNode(id=nid, label=note.title, title=note.title, url=_note_public_url(note), group="note")
                )

            for link in note.outgoing_links:
                if link.is_resolved and link.target_id and not link.target_text.startswith("http"):
                    tid = f"note:{link.target_id}"
                    edges.append(GraphEdge(source=nid, target=tid, kind="link" if not link.is_embed else "embed"))

            for tag in note.tags:
                tid = f"tag:{tag.lower()}"
                if tid not in seen_tags:
                    seen_tags.add(tid)
                    nodes.append(
                        GraphNode(id=tid, label=f"#{tag}", title=f"#{tag}", url=f"/tags/{tag.lower()}", group="tag")
                    )
                edges.append(GraphEdge(source=nid, target=tid, kind="tag"))

        return GraphData(nodes=nodes, edges=edges)

    def _build_search_documents(
        self, notes: list[NoteRecord], text_pages: list[TextPageRecord]
    ) -> list[dict[str, object]]:
        docs: list[dict[str, object]] = []
        for note in notes:
            docs.append({
                "id": note.content_hash,
                "title": note.title,
                "path": note.rel_path.as_posix(),
                "url": _note_public_url(note),
                "content": note.plain_text[:5000],
                "tags": list(note.tags),
                "headings": [h.text for h in note.headings],
                "aliases": note.aliases,
                "excerpt": note.excerpt,
            })
        for tp in text_pages:
            docs.append({
                "id": tp.id,
                "title": tp.title,
                "path": tp.rel_path.as_posix(),
                "url": tp.url_path,
                "content": tp.plain_text[:5000],
                "tags": [],
                "headings": [],
                "aliases": [],
                "excerpt": tp.excerpt,
            })
        return docs


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:100]


def _note_public_url(note: NoteRecord) -> str:
    permalink = note.frontmatter.get("permalink")
    if permalink:
        return "/" + str(permalink).lstrip("/")
    return note.url_path
