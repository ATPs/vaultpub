from __future__ import annotations

import fnmatch
import hashlib
import os
import re
from pathlib import Path, PurePosixPath

from vaultpub.core.config import PublisherConfig
from vaultpub.core.exceptions import PathTraversalError
from vaultpub.core.models import AttachmentRecord, NavNode, NoteRecord, TextPageRecord
from vaultpub.core.paths import (
    directory_path_to_url_path,
    file_display_name,
    generate_note_id,
    normalize_rel_path,
    rel_path_to_url_path,
)
from vaultpub.core.security import (
    ALWAYS_FORBIDDEN,
    is_force_included,
    is_text_file,
    infer_language,
)


class VaultScanner:
    """Scans a vault directory to discover notes, attachments, and build the nav tree."""

    def __init__(self, config: PublisherConfig) -> None:
        self.config = config

    def scan(self) -> tuple[list[NoteRecord], list[AttachmentRecord], list[TextPageRecord], NavNode]:
        notes: list[NoteRecord] = []
        attachments: list[AttachmentRecord] = []
        text_pages: list[TextPageRecord] = []
        root = self.config.vault_path.resolve()
        compiled_exclude = getattr(self.config, "_compiled_force_exclude", [])

        for dirpath_str, dirnames, filenames in os.walk(root, followlinks=self.config.follow_symlinks):
            dirpath = Path(dirpath_str)

            # Filter dirnames for os.walk pruning
            kept_dirs = []
            for d in dirnames:
                if d in ALWAYS_FORBIDDEN:
                    continue
                if self._is_hidden(d) and not self.config.hidden_file_access:
                    continue
                # In publish_true mode, don't prune excluded folders (they might contain publish:true notes)
                if self.config.publish_property_mode == "publish_true":
                    kept_dirs.append(d)
                    continue
                if d in self.config.exclude_folders:
                    continue
                # Prune directories matching force_exclude_regexes
                if compiled_exclude:
                    try:
                        dir_rel = normalize_rel_path(dirpath / d, root)
                    except PathTraversalError:
                        continue
                    if any(pat.search(dir_rel) for pat in compiled_exclude):
                        continue
                kept_dirs.append(d)
            dirnames[:] = kept_dirs

            for fname in sorted(filenames):
                fpath = dirpath / fname

                if not self.config.follow_symlinks and fpath.is_symlink():
                    continue
                if self._is_hidden(fname) and not self.config.hidden_file_access:
                    continue
                if self._is_excluded_by_glob(fpath, root):
                    continue

                try:
                    rel = normalize_rel_path(fpath, root)
                except PathTraversalError:
                    continue

                # Force-exclude regex check
                if compiled_exclude and any(pat.search(rel) for pat in compiled_exclude):
                    continue

                stat = fpath.stat()
                ext = fpath.suffix.lower()

                if ext == ".md":
                    if fpath.stat().st_size > self.config.max_markdown_size_bytes:
                        continue
                    note = self._read_note(fpath, rel, stat)
                    if self._should_publish(note):
                        notes.append(note)
                elif self._is_force_included_text(fpath, rel):
                    tp = self._read_text_page(fpath, rel, ext, stat)
                    text_pages.append(tp)
                elif ext.lstrip(".") in self.config.allowed_attachment_types:
                    if self.config.max_attachment_size_bytes and stat.st_size > self.config.max_attachment_size_bytes:
                        continue
                    att = self._read_attachment(fpath, rel, stat)
                    attachments.append(att)

        nav = self._build_nav_tree(notes, text_pages)
        return notes, attachments, text_pages, nav

    def _is_hidden(self, name: str) -> bool:
        return name.startswith(".")

    def _is_excluded_by_glob(self, fpath: Path, root: Path) -> bool:
        if not self.config.exclude_globs:
            return False
        try:
            rel = str(fpath.relative_to(root))
        except ValueError:
            return True
        return any(fnmatch.fnmatch(rel, pattern) for pattern in self.config.exclude_globs)

    def _is_force_included_text(self, fpath: Path, rel: str) -> bool:
        """Check if a non-.md file should be included as a text page."""
        if not is_force_included(rel, self.config):
            return False
        if fpath.stat().st_size > self.config.max_markdown_size_bytes:
            return False
        return is_text_file(fpath)

    def _read_note(self, fpath: Path, rel: str, stat: os.stat_result) -> NoteRecord:
        content = fpath.read_text(encoding="utf-8-sig")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        stem = fpath.stem
        url_path = rel_path_to_url_path(rel)
        note_id = generate_note_id(rel)
        ppath = PurePosixPath(rel)

        # Attempt frontmatter extraction
        fm: dict = {}
        body = content
        title = stem
        aliases: list[str] = []
        tags: set[str] = set()

        # Simple frontmatter extraction (detailed parsing in frontmatter module)
        fm, body = _extract_frontmatter_simple(content)
        if "title" in fm:
            title = str(fm["title"])
        if "aliases" in fm:
            raw = fm["aliases"]
            aliases = [str(a) for a in raw] if isinstance(raw, list) else [str(raw)]
        if "tags" in fm:
            raw_tags = fm["tags"]
            if isinstance(raw_tags, list):
                tags = {str(t) for t in raw_tags}
            elif isinstance(raw_tags, str):
                tags = {t.strip() for t in raw_tags.split(",") if t.strip()}

        excerpt = body[:300].replace("\n", " ").strip()

        return NoteRecord(
            id=note_id,
            rel_path=ppath,
            url_path=url_path,
            title=title,
            stem=stem,
            frontmatter=fm,
            aliases=aliases,
            tags=tags,
            raw_markdown=content,
            plain_text=body[:2000],
            excerpt=excerpt,
            ctime_ns=int(stat.st_ctime_ns),
            mtime_ns=int(stat.st_mtime_ns),
            size=stat.st_size,
            content_hash=content_hash,
        )

    def _read_text_page(self, fpath: Path, rel: str, ext: str, stat: os.stat_result) -> TextPageRecord:
        content = fpath.read_text(encoding="utf-8-sig")
        stem = fpath.stem
        url_path = "/" + PurePosixPath(rel).as_posix()
        page_id = generate_note_id(rel)
        language = infer_language(ext)
        plain = content[:2000]
        excerpt = content[:300].replace("\n", " ").strip()

        return TextPageRecord(
            id=page_id,
            rel_path=PurePosixPath(rel),
            url_path=url_path,
            title=file_display_name(rel),
            stem=stem,
            language=language,
            raw_text=content,
            plain_text=plain,
            excerpt=excerpt,
            size=stat.st_size,
            mtime_ns=int(stat.st_mtime_ns),
            ctime_ns=int(stat.st_ctime_ns),
        )

    def _read_attachment(self, fpath: Path, rel: str, stat: os.stat_result) -> AttachmentRecord:
        ext = fpath.suffix.lower().lstrip(".")
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp",
            "pdf": "application/pdf",
            "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
            "mp4": "video/mp4", "webm": "video/webm",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")
        url_path = "/assets/" + PurePosixPath(rel).as_posix()
        att_id = generate_note_id(rel)

        return AttachmentRecord(
            id=att_id,
            rel_path=PurePosixPath(rel),
            url_path=url_path,
            mime_type=mime_type,
            size=stat.st_size,
            mtime_ns=int(stat.st_mtime_ns),
        )

    def _should_publish(self, note: NoteRecord) -> bool:
        fm = note.frontmatter
        mode = self.config.publish_property_mode

        # Check excluded folders: publish:true can override only in publish_true mode
        rel = note.rel_path.as_posix()
        top_dir = rel.split("/")[0] if "/" in rel else ""
        in_excluded = top_dir in self.config.exclude_folders

        if in_excluded and mode != "publish_true":
            return False
        if in_excluded and mode == "publish_true" and fm.get("publish") is True:
            return True
        if in_excluded:
            return False

        if mode == "publish_true":
            return fm.get("publish") is True
        # mode "publish_false_hides": hide when publish is explicitly false
        # mode "all": publish everything
        return not (mode == "publish_false_hides" and fm.get("publish") is False)

    def _build_nav_tree(self, notes: list[NoteRecord], text_pages: list[TextPageRecord]) -> NavNode:
        root = NavNode(label="/", path=".", url="/", is_dir=True)
        nav_hidden = set(self.config.nav_hidden)

        # Sort notes into directory structure
        for note in sorted(notes, key=lambda n: n.rel_path.as_posix()):
            if note.stem in nav_hidden or note.rel_path.as_posix() in nav_hidden:
                continue
            parts = note.rel_path.parts
            current = root
            for _i, part in enumerate(parts[:-1]):
                child = _find_or_create_dir(current, part)
                current = child
            # Add note as leaf
            current.children.append(NavNode(
                label=file_display_name(note.rel_path),
                path=note.rel_path.as_posix(),
                url=note.url_path,
            ))

        # Add text pages to nav
        for tp in sorted(text_pages, key=lambda t: t.rel_path.as_posix()):
            if tp.stem in nav_hidden or tp.rel_path.as_posix() in nav_hidden:
                continue
            parts = tp.rel_path.parts
            current = root
            for _i, part in enumerate(parts[:-1]):
                child = _find_or_create_dir(current, part)
                current = child
            current.children.append(NavNode(
                label=file_display_name(tp.rel_path),
                path=tp.rel_path.as_posix(),
                url=tp.url_path,
            ))

        # Sort: dirs first, then files, both alphabetically
        root.children.sort(key=lambda n: (not n.is_dir, n.label.lower()))
        self._sort_nav(root)
        return root

    def _sort_nav(self, node: NavNode) -> None:
        for child in node.children:
            self._sort_nav(child)
        node.children.sort(key=lambda n: (not n.is_dir, n.label.lower()))

    def resolve_home(self, notes: list[NoteRecord]) -> NoteRecord | None:
        """Resolve the home/index page."""
        if self.config.home_file:
            for note in notes:
                if note.stem == self.config.home_file or note.rel_path.as_posix() == self.config.home_file + ".md":
                    return note

        candidates = self.config.default_home_candidates
        for candidate_stem in candidates:
            for note in notes:
                if note.stem == candidate_stem:
                    return note

        # First visible markdown
        if notes:
            return notes[0]

        return None


def _find_or_create_dir(parent: NavNode, name: str) -> NavNode:
    for child in parent.children:
        if child.is_dir and child.label == name:
            return child
    parent_path = "" if parent.path in ("", ".") else parent.path
    dir_path = f"{parent_path}/{name}" if parent_path else name
    dir_node = NavNode(label=name, path=dir_path, url=directory_path_to_url_path(dir_path), is_dir=True)
    parent.children.append(dir_node)
    return dir_node


def _extract_frontmatter_simple(content: str) -> tuple[dict, str]:
    """Simple frontmatter extraction. Full parsing is in the frontmatter module."""
    if not content.startswith("---"):
        return {}, content
    lines = content.split("\n")
    if lines[0].strip() != "---":
        return {}, content
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, content

    import yaml

    try:
        fm_text = "\n".join(lines[1:end_idx])
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}

    body = "\n".join(lines[end_idx + 1:])
    return fm, body
