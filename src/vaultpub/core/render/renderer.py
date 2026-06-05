"""HTML rendering pipeline.

Uses a placeholder-based approach so raw HTML survives markdown-it in safe mode:
1. Replace wikilinks, embeds, callouts, mermaid, math with placeholders
2. Render markdown to HTML
3. Replace placeholders with final HTML
4. Sanitize
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from html import escape, unescape
from pathlib import PurePosixPath

from vaultpub.core.attachments import (
    attachment_download_name,
    is_download_only_attachment,
    is_image_attachment,
)
from vaultpub.core.config import PublisherConfig
from vaultpub.core.frontmatter import parse_frontmatter
from vaultpub.core.models import AttachmentRecord, NoteRecord, TextPageRecord, VaultIndex
from vaultpub.core.parser.callouts import parse_callout_block, render_callout_html
from vaultpub.core.parser.markdown import render_markdown
from vaultpub.core.parser.obsidian_links import (
    find_wikilinks,
    parse_wikilink_target,
    strip_obsidian_comments,
)
from vaultpub.core.paths import file_display_name
from vaultpub.core.render.sanitize import add_external_link_attrs, sanitize_html

_PLACEHOLDER_RE = re.compile(r"VAULTPUB_PLACEHOLDER_(\d+)")
_PLACEHOLDER_PARAGRAPH_RE = re.compile(r"<p>\s*VAULTPUB_PLACEHOLDER_(\d+)\s*</p>")
_LOCAL_URL_ATTR_RE = re.compile(r'(?P<attr>\s(?:href|src)=["\'])(?P<url>[^"\']+)(?P<quote>["\'])')
_ANCHOR_TAG_RE = re.compile(
    r'<a\b(?P<before>[^>]*)href=(?P<quote>["\'])(?P<url>[^"\']+)(?P=quote)(?P<after>[^>]*)>(?P<body>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_IMG_TAG_RE = re.compile(r"<img\b(?P<attrs>[^>]*)/?>", re.IGNORECASE)
_PASSTHROUGH_URL_PREFIXES = ("/assets/", "/static/", "/api/")
_PASSTHROUGH_URLS = {"/graph.json", "/search-index.json"}
_AUDIO_EXTS = {"mp3", "wav", "ogg", "flac", "m4a"}
_VIDEO_EXTS = {"mp4", "webm", "mov", "avi"}


@dataclass(frozen=True)
class _ResolvedTarget:
    kind: str
    url: str
    note: NoteRecord | None = None
    text_page: TextPageRecord | None = None
    attachment: AttachmentRecord | None = None


class Renderer:
    """Renders notes to HTML using the vault index."""

    def __init__(self, config: PublisherConfig, index: VaultIndex) -> None:
        self.config = config
        self.index = index

    def render_note(self, note: NoteRecord, embed_depth: int = 0) -> str:
        _frontmatter, content, _body_start = parse_frontmatter(note.raw_markdown)
        content = strip_obsidian_comments(content)
        placeholders: dict[int, str] = {}
        counter = 0

        # Phase 1: Preprocess — replace raw-HTML-producing syntax with placeholders
        content, counter = self._preprocess_mermaid(content, counter, placeholders)
        content, counter = self._preprocess_math(content, counter, placeholders)
        content, counter = self._preprocess_callouts(content, counter, placeholders)
        content, counter = self._preprocess_wikilinks(content, note, counter, placeholders, embed_depth)

        # Phase 2: Render markdown
        html = render_markdown(
            content,
            strict_line_breaks=self.config.strict_line_breaks,
            html_safe_mode=self.config.html_safe_mode,
        )

        # Phase 3: Add anchors to headings from this note before restoring embedded HTML.
        html = self._add_heading_anchors(html, note)

        # Phase 4: Restore placeholders
        html = self._restore_placeholders(html, placeholders)

        # Phase 5: Post-processing
        html = self._rewrite_local_img_tags(html, note)
        html = self._rewrite_local_anchor_tags(html, note)
        html = self._rewrite_local_html_urls(html, note)

        # Phase 6: Sanitize and add external link attrs
        if self.config.html_safe_mode:
            html = sanitize_html(html)
        html = add_external_link_attrs(html)

        return html

    def _placeholder(self, counter: int) -> str:
        return f"VAULTPUB_PLACEHOLDER_{counter}"

    def _restore_placeholders(self, html: str, placeholders: dict[int, str]) -> str:
        def _replace(m: re.Match) -> str:
            idx = int(m.group(1))
            return placeholders.get(idx, m.group(0))

        html = _PLACEHOLDER_PARAGRAPH_RE.sub(_replace, html)
        return _PLACEHOLDER_RE.sub(_replace, html)

    def _preprocess_wikilinks(
        self,
        content: str,
        source_note: NoteRecord,
        counter: int,
        placeholders: dict[int, str],
        embed_depth: int,
    ) -> tuple[str, int]:
        replacements: list[tuple[int, int, str]] = []

        for start, end, raw_target, is_embed in find_wikilinks(content):
            target_text, anchor, display_text, size = parse_wikilink_target(raw_target)

            # Self-reference anchor
            if target_text == "" and anchor:
                href = (
                    f"#{_slugify(anchor.lstrip('^'))}"
                    if not anchor.startswith("^")
                    else f"#^{anchor.lstrip('^')}"
                )
                dtext = display_text or anchor
                replacements.append((start, end, f"[{dtext}]({href})"))
                continue

            resolved = self._resolve_target(target_text, source_note.rel_path)

            if resolved.attachment is not None:
                dtext = display_text or file_display_name(resolved.attachment.rel_path)
                if is_embed:
                    placeholders[counter] = self._render_attachment_embed(
                        resolved.attachment,
                        size=size,
                        label=dtext,
                    )
                    replacements.append((start, end, self._placeholder(counter)))
                    counter += 1
                else:
                    replacements.append((start, end, f"[{dtext}]({resolved.url})"))
                continue

            if resolved.text_page is not None:
                dtext = display_text or file_display_name(resolved.text_page.rel_path)
                if is_embed:
                    placeholders[counter] = self._render_text_page_embed(resolved.text_page)
                    replacements.append((start, end, self._placeholder(counter)))
                    counter += 1
                else:
                    link_html = (
                        f'<a href="{escape(resolved.url, quote=True)}" class="internal-link">{escape(dtext)}</a>'
                    )
                    placeholders[counter] = link_html
                    replacements.append((start, end, self._placeholder(counter)))
                    counter += 1
                continue

            if resolved.note is not None:
                target_note = resolved.note
                resolved_url = resolved.url
                if anchor:
                    sep = "#^" if anchor.startswith("^") else "#"
                    resolved_url += sep + (anchor.lstrip("^") if anchor.startswith("^") else _slugify(anchor))
                dtext = display_text or file_display_name(target_note.rel_path)
                if is_embed:
                    if embed_depth >= 5:
                        embed_html = '<div class="embed-error">Maximum embed depth exceeded</div>'
                    elif target_note.id == source_note.id:
                        embed_html = '<div class="embed-error">Circular embed detected</div>'
                    else:
                        embedded_body = self.render_note(target_note, embed_depth=embed_depth + 1)
                        embed_source = escape(target_note.url_path, quote=True)
                        embed_html = (
                            f'<div class="embed-wrapper" data-embed-source="{embed_source}">{embedded_body}</div>'
                        )
                    placeholders[counter] = embed_html
                    replacements.append((start, end, self._placeholder(counter)))
                    counter += 1
                else:
                    link_html = (
                        f'<a href="{escape(resolved_url, quote=True)}" class="internal-link">'
                        f"{escape(dtext)}</a>"
                    )
                    placeholders[counter] = link_html
                    replacements.append((start, end, self._placeholder(counter)))
                    counter += 1
            else:
                dtext = display_text or _default_file_label(target_text)
                resolved_target = target_text
                if "|" in raw_target and "#" not in raw_target.split("|")[0]:
                    resolved_target = raw_target.split("|", 1)[0]
                placeholders[counter] = (
                    f'<a class="internal-link is-unresolved" data-target="{escape(resolved_target, quote=True)}">'
                    f"{escape(dtext)}</a>"
                )
                replacements.append((start, end, self._placeholder(counter)))
                counter += 1

        for start, end, repl in reversed(replacements):
            content = content[:start] + repl + content[end:]

        return content, counter

    def _rewrite_local_img_tags(self, html: str, source_note: NoteRecord) -> str:
        def _replace(match: re.Match[str]) -> str:
            attrs = match.group("attrs")
            src = _extract_html_attr(attrs, "src")
            if not src:
                return match.group(0)

            resolved = self._resolve_target(unescape(src), source_note.rel_path)
            if resolved.kind not in {"note", "text_page", "attachment"}:
                return match.group(0)

            alt = unescape(_extract_html_attr(attrs, "alt") or "")
            label = alt or _resolved_target_label(resolved, src)

            if resolved.attachment is not None and is_image_attachment(resolved.attachment.rel_path):
                return _replace_html_attr(match.group(0), "src", resolved.url)

            download_name = None
            if resolved.attachment is not None and is_download_only_attachment(resolved.attachment.rel_path):
                download_name = attachment_download_name(resolved.attachment.rel_path)

            return _render_anchor_html(resolved.url, label, download_name=download_name)

        return _IMG_TAG_RE.sub(_replace, html)

    def _rewrite_local_anchor_tags(self, html: str, source_note: NoteRecord) -> str:
        def _replace(match: re.Match[str]) -> str:
            url = match.group("url")
            resolved = self._resolve_target(unescape(url), source_note.rel_path)
            if resolved.kind not in {"note", "text_page", "attachment"}:
                return match.group(0)

            download_attr = ""
            if resolved.attachment is not None and is_download_only_attachment(resolved.attachment.rel_path):
                download_name = attachment_download_name(resolved.attachment.rel_path)
                combined_attrs = match.group("before") + match.group("after")
                if " download=" not in combined_attrs.lower():
                    download_attr = f' download="{escape(download_name, quote=True)}"'

            return (
                f'<a{match.group("before")}href="{escape(resolved.url, quote=True)}"'
                f'{match.group("after")}{download_attr}>{match.group("body")}</a>'
            )

        return _ANCHOR_TAG_RE.sub(_replace, html)

    def _rewrite_local_html_urls(self, html: str, source_note: NoteRecord) -> str:
        def _replace(match: re.Match[str]) -> str:
            url = match.group("url")
            resolved = self._resolve_target(url, source_note.rel_path)
            if resolved.kind not in {"note", "text_page", "attachment"}:
                return match.group(0)
            return f'{match.group("attr")}{escape(resolved.url, quote=True)}{match.group("quote")}'

        return _LOCAL_URL_ATTR_RE.sub(_replace, html)

    def _resolve_target(self, target: str, source_path: PurePosixPath) -> _ResolvedTarget:
        if (
            not target
            or target.startswith("#")
            or target.startswith("//")
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)
            or target.startswith(_PASSTHROUGH_URL_PREFIXES)
            or target in _PASSTHROUGH_URLS
        ):
            return _ResolvedTarget(kind="passthrough", url=target)

        path_part, suffix = _split_url_parts(target)
        normalized = self._normalize_target_path(path_part, source_path)
        if normalized is None:
            return _ResolvedTarget(kind="unresolved", url=target)

        note = self._resolve_note(path_part, normalized)
        if note is not None:
            return _ResolvedTarget(kind="note", url=_note_public_url(note) + suffix, note=note)

        text_page = self.index.text_pages_by_path.get(normalized)
        if text_page is not None:
            return _ResolvedTarget(kind="text_page", url=text_page.url_path + suffix, text_page=text_page)

        attachment = self.index.attachments_by_path.get(normalized)
        if attachment is not None:
            return _ResolvedTarget(kind="attachment", url=attachment.url_path + suffix, attachment=attachment)

        return _ResolvedTarget(kind="unresolved", url=target)

    def _normalize_target_path(self, target: str, source_path: PurePosixPath) -> str | None:
        candidate = (
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.join(source_path.parent.as_posix(), target)
        )
        normalized = posixpath.normpath(candidate)
        if normalized in ("", "."):
            return None
        if normalized == ".." or normalized.startswith("../"):
            return None
        return PurePosixPath(normalized).as_posix()

    def _resolve_note(self, raw_target: str, normalized_target: str) -> NoteRecord | None:
        notes_by_id = self.index.notes_by_id
        notes_by_path = self.index.notes_by_path
        notes_by_stem = self.index.notes_by_stem
        notes_by_alias = self.index.notes_by_alias

        if normalized_target in notes_by_path:
            return notes_by_id[notes_by_path[normalized_target]]

        normalized_path = PurePosixPath(normalized_target)
        if not normalized_path.suffix:
            md_target = f"{normalized_target}.md"
            if md_target in notes_by_path:
                return notes_by_id[notes_by_path[md_target]]

        raw_path = PurePosixPath(raw_target.lstrip("/"))
        if raw_path.suffix not in ("", ".md"):
            return None

        stem = raw_path.stem or normalized_path.stem
        if stem in notes_by_stem:
            return notes_by_id[notes_by_stem[stem][0]]

        for alias_key in {raw_target.lower().lstrip("/"), normalized_target.lower()}:
            if alias_key in notes_by_alias:
                return notes_by_id[notes_by_alias[alias_key][0]]

        return None

    def _render_attachment_embed(self, attachment: AttachmentRecord, size: str | None = None, label: str = "") -> str:
        ext = attachment.rel_path.suffix.lstrip(".").lower()
        if is_image_attachment(attachment.rel_path):
            size_attr = ""
            if size:
                parts = size.split("x")
                size_attr = (
                    f' width="{parts[0]}"'
                    if len(parts) == 1
                    else f' width="{parts[0]}" height="{parts[1]}"'
                )
            alt = escape(label, quote=True)
            return (
                f'<img src="{escape(attachment.url_path, quote=True)}" alt="{alt}"'
                f'{size_attr} class="embed-image">'
            )
        if ext in _AUDIO_EXTS:
            return f'<audio controls src="{escape(attachment.url_path, quote=True)}" class="embed-audio"></audio>'
        if ext in _VIDEO_EXTS:
            return f'<video controls src="{escape(attachment.url_path, quote=True)}" class="embed-video"></video>'
        if ext == "pdf":
            return f'<iframe src="{escape(attachment.url_path, quote=True)}" class="pdf-embed"></iframe>'
        download_name = (
            attachment_download_name(attachment.rel_path)
            if is_download_only_attachment(attachment.rel_path)
            else None
        )
        return _render_anchor_html(attachment.url_path, label, download_name=download_name)

    def _render_text_page_embed(self, text_page: TextPageRecord) -> str:
        code_class = f' class="language-{text_page.language}"' if text_page.language else ""
        embed_source = escape(text_page.url_path, quote=True)
        title = escape(text_page.title)
        code_body = escape(text_page.raw_text)
        return f"""\
<div class="embed-wrapper" data-embed-source="{embed_source}">
  <div class="text-page-embed">
    <p class="text-page-embed-title"><a href="{embed_source}" class="internal-link">{title}</a></p>
    <pre><code{code_class}>{code_body}</code></pre>
  </div>
</div>"""

    def _preprocess_callouts(self, content: str, counter: int, placeholders: dict[int, str]) -> tuple[str, int]:
        lines = content.split("\n")
        result_lines: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith(">") and "[!" in line:
                callout, next_i = parse_callout_block(lines, i)
                if callout:
                    placeholders[counter] = render_callout_html(callout)
                    result_lines.append(self._placeholder(counter))
                    counter += 1
                    i = next_i
                    continue
            result_lines.append(line)
            i += 1
        return "\n".join(result_lines), counter

    def _preprocess_mermaid(self, content: str, counter: int, placeholders: dict[int, str]) -> tuple[str, int]:
        """Replace ```mermaid blocks with placeholders."""
        fence_re = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)

        def _replace(m: re.Match) -> str:
            nonlocal counter
            diagram = m.group(1).strip()
            placeholders[counter] = f'<div class="mermaid">{diagram}</div>'
            placeholder = self._placeholder(counter)
            counter += 1
            return placeholder

        result = fence_re.sub(_replace, content)
        return result, counter

    def _preprocess_math(self, content: str, counter: int, placeholders: dict[int, str]) -> tuple[str, int]:
        """Replace $$math$$ and $math$ with placeholders."""
        # Block math first ($$...$$)
        block_re = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

        def _replace_block(m: re.Match) -> str:
            nonlocal counter
            formula = m.group(1).strip()
            placeholders[counter] = f'<div class="math block">{formula}</div>'
            placeholder = self._placeholder(counter)
            counter += 1
            return placeholder

        result = block_re.sub(_replace_block, content)

        # Inline math ($...$)
        inline_re = re.compile(r"\$(.+?)\$")

        def _replace_inline(m: re.Match) -> str:
            nonlocal counter
            formula = m.group(1).strip()
            placeholders[counter] = f'<span class="math inline">{formula}</span>'
            placeholder = self._placeholder(counter)
            counter += 1
            return placeholder

        result = inline_re.sub(_replace_inline, result)
        return result, counter

    def _add_heading_anchors(self, html: str, note: NoteRecord) -> str:
        headings = iter(note.headings)

        def _add_anchor(match: re.Match) -> str:
            level = int(match.group("level"))
            attrs = match.group("attrs")
            body = match.group("body")
            heading = next(headings, None)
            slug = heading.slug if heading is not None else _slugify(_strip_html_tags(body))
            safe_slug = escape(slug, quote=True)
            attrs = re.sub(r'\s+id=(["\']).*?\1', "", attrs, flags=re.IGNORECASE | re.DOTALL)
            return (
                f'<h{level}{attrs} id="{safe_slug}">{body} '
                f'<a class="heading-anchor" href="#{safe_slug}">#</a></h{level}>'
            )

        heading_re = re.compile(
            r"<h(?P<level>[1-6])(?P<attrs>[^>]*)>(?P<body>.*?)</h(?P=level)>",
            re.DOTALL,
        )
        return heading_re.sub(_add_anchor, html)

    def render_article_html(self, note: NoteRecord, current_path: str | None = None) -> str:
        body = self.render_note(note)
        page_path = escape(current_path or note.url_path, quote=True)

        return f"""\
<article class="note" data-note-id="{note.id}" data-note-path="{page_path}" data-current-path="{page_path}">
  <div class="markdown-body">{body}</div>
</article>"""

    def render_page_html(self, note: NoteRecord) -> str:
        backlinks_html = self.render_backlinks_html(note)
        toc_html = self.render_toc_html(note)

        return f"""\
{self.render_article_html(note)}
{toc_html}
{backlinks_html}"""

    def render_backlinks_html(self, note: NoteRecord) -> str:
        if not note.backlinks:
            return ""
        links = []
        for bid in sorted(note.backlinks):
            bl_note = self.index.notes_by_id.get(bid)
            if bl_note:
                links.append(
                    '<li><a href="'
                    f'{_note_public_url(bl_note)}" class="internal-link">{escape(file_display_name(bl_note.rel_path))}'
                    "</a></li>"
                )
        if not links:
            return ""
        return f"""\
<section class="backlinks">
  <h3>Backlinks</h3>
  <ul>{"".join(links)}</ul>
</section>"""

    def render_toc_html(self, note: NoteRecord) -> str:
        if not note.headings:
            return ""
        items = []
        for h in note.headings:
            indent = "  " * (h.level - 1)
            items.append(f'{indent}<li><a href="#{h.slug}">{h.text}</a></li>')
        return f"""\
<nav class="toc">
  <h3>Contents</h3>
  <ul>{"".join(items)}</ul>
</nav>"""


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:100]


def _strip_html_tags(text: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", text))


def _split_url_parts(url: str) -> tuple[str, str]:
    path_part, frag_sep, fragment = url.partition("#")
    path_part, query_sep, query = path_part.partition("?")
    suffix = ""
    if query_sep:
        suffix += f"?{query}"
    if frag_sep:
        suffix += f"#{fragment}"
    return path_part, suffix


def _extract_html_attr(attrs: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}=(["\'])(.*?)\1', attrs, re.IGNORECASE | re.DOTALL)
    if match is None:
        return None
    return match.group(2)


def _replace_html_attr(tag: str, name: str, value: str) -> str:
    pattern = re.compile(
        rf'(?P<prefix>\b{re.escape(name)}=)(?P<quote>["\'])(?P<value>.*?)(?P=quote)',
        re.IGNORECASE | re.DOTALL,
    )

    def _replace(match: re.Match[str]) -> str:
        return f'{match.group("prefix")}"{escape(value, quote=True)}"'

    return pattern.sub(_replace, tag, count=1)


def _render_anchor_html(url: str, label: str, download_name: str | None = None) -> str:
    safe_label = escape(label)
    safe_url = escape(url, quote=True)
    download_attr = f' download="{escape(download_name, quote=True)}"' if download_name else ""
    return f'<a href="{safe_url}"{download_attr}>{safe_label}</a>'


def _note_public_url(note: NoteRecord) -> str:
    return note.url_path


def _resolved_target_label(resolved: _ResolvedTarget, raw_target: str) -> str:
    if resolved.attachment is not None:
        return attachment_download_name(resolved.attachment.rel_path)
    if resolved.text_page is not None:
        return file_display_name(resolved.text_page.rel_path)
    if resolved.note is not None:
        return file_display_name(resolved.note.rel_path)
    path_part, _suffix = _split_url_parts(raw_target)
    return file_display_name(path_part or raw_target)


def _default_file_label(target_text: str) -> str:
    if not target_text:
        return ""
    target_path = PurePosixPath(target_text)
    if target_path.suffix:
        return target_path.name
    return f"{target_path.name}.md"
