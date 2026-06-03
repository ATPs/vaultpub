"""HTML rendering pipeline.

Uses a placeholder-based approach so raw HTML survives markdown-it in safe mode:
1. Replace wikilinks, embeds, callouts, mermaid, math with placeholders
2. Render markdown to HTML
3. Replace placeholders with final HTML
4. Sanitize
"""
from __future__ import annotations

import re
from html import escape
from pathlib import PurePosixPath

from vaultpub.core.config import PublisherConfig
from vaultpub.core.frontmatter import parse_frontmatter
from vaultpub.core.models import NoteRecord, VaultIndex
from vaultpub.core.parser.callouts import parse_callout_block, render_callout_html
from vaultpub.core.parser.markdown import render_markdown
from vaultpub.core.parser.obsidian_links import (
    find_wikilinks,
    parse_wikilink_target,
    strip_obsidian_comments,
)
from vaultpub.core.render.sanitize import add_external_link_attrs, sanitize_html

_PLACEHOLDER_RE = re.compile(r"VAULTPUB_PLACEHOLDER_(\d+)")
_PLACEHOLDER_PARAGRAPH_RE = re.compile(r"<p>\s*VAULTPUB_PLACEHOLDER_(\d+)\s*</p>")


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

        # Phase 3: Restore placeholders
        html = self._restore_placeholders(html, placeholders)

        # Phase 4: Post-processing
        html = self._add_heading_anchors(html)

        # Phase 5: Sanitize and add external link attrs
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

            att_ext = PurePosixPath(target_text).suffix.lstrip(".").lower()
            is_attachment = att_ext in self.config.allowed_attachment_types

            # Image/audio/video embed: produces raw HTML, use placeholder
            if is_embed and is_attachment:
                att_url = "/assets/" + target_text
                if att_ext in ("png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico"):
                    size_attr = ""
                    if size:
                        parts = size.split("x")
                        if len(parts) == 1:
                            size_attr = f' width="{parts[0]}"'
                        else:
                            size_attr = f' width="{parts[0]}" height="{parts[1]}"'
                    alt = escape(display_text or target_text, quote=True)
                    html_str = f'<img src="{escape(att_url, quote=True)}" alt="{alt}"{size_attr} class="embed-image">'
                elif att_ext in ("mp3", "wav", "ogg", "flac", "m4a"):
                    html_str = f'<audio controls src="{escape(att_url, quote=True)}" class="embed-audio"></audio>'
                elif att_ext in ("mp4", "webm", "mov", "avi"):
                    html_str = f'<video controls src="{escape(att_url, quote=True)}" class="embed-video"></video>'
                elif att_ext == "pdf":
                    html_str = f'<iframe src="{escape(att_url, quote=True)}" class="pdf-embed"></iframe>'
                else:
                    html_str = f'<a href="{escape(att_url, quote=True)}">{escape(display_text or target_text)}</a>'

                placeholders[counter] = html_str
                replacements.append((start, end, self._placeholder(counter)))
                counter += 1
                continue

            # Attachment link (no embed): simple markdown link
            if is_attachment and not is_embed:
                att_url = "/assets/" + target_text
                dtext = display_text or target_text
                replacements.append((start, end, f"[{dtext}]({att_url})"))
                continue

            # Resolve note link
            target_note = self._resolve_note(target_text, source_note)

            if target_note:
                resolved_url = _note_public_url(target_note)
                if anchor:
                    sep = "#^" if anchor.startswith("^") else "#"
                    resolved_url += sep + (anchor.lstrip("^") if anchor.startswith("^") else _slugify(anchor))
                dtext = display_text or target_text or PurePosixPath(target_text).stem
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
                dtext = display_text or target_text or PurePosixPath(target_text).stem
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

    def _resolve_note(self, target_text: str, source_note: NoteRecord) -> NoteRecord | None:
        notes_by_id = self.index.notes_by_id
        notes_by_path = self.index.notes_by_path
        notes_by_stem = self.index.notes_by_stem
        notes_by_alias = self.index.notes_by_alias

        target_clean = target_text if "." in target_text else target_text + ".md"
        if target_clean in notes_by_path:
            return notes_by_id[notes_by_path[target_clean]]
        if target_text in notes_by_path:
            return notes_by_id[notes_by_path[target_text]]

        note_dir = source_note.rel_path.parent
        rel_target = (note_dir / target_text).as_posix()
        if rel_target in notes_by_path:
            return notes_by_id[notes_by_path[rel_target]]
        if rel_target + ".md" in notes_by_path:
            return notes_by_id[notes_by_path[rel_target + ".md"]]

        stem = PurePosixPath(target_text).stem
        if stem in notes_by_stem:
            return notes_by_id[notes_by_stem[stem][0]]

        alias_key = target_text.lower()
        if alias_key in notes_by_alias:
            return notes_by_id[notes_by_alias[alias_key][0]]

        return None

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

    def _add_heading_anchors(self, html: str) -> str:
        def _add_anchor(match: re.Match) -> str:
            level = len(match.group(1))
            text = match.group(2)
            slug = _slugify(text)
            return f'<h{level} id="{slug}">{text} <a class="heading-anchor" href="#{slug}">#</a></h{level}>'

        return re.sub(r"<h([1-6])>(.+?)</h\1>", _add_anchor, html)

    def render_page_html(self, note: NoteRecord) -> str:
        body = self.render_note(note)
        backlinks_html = self._render_backlinks(note)
        toc_html = self._render_toc(note)

        return f"""\
<article class="note" data-note-id="{note.id}" data-note-path="{note.url_path}">
  <div class="markdown-body">{body}</div>
  {toc_html}
  {backlinks_html}
</article>"""

    def _render_backlinks(self, note: NoteRecord) -> str:
        if not note.backlinks:
            return ""
        links = []
        for bid in sorted(note.backlinks):
            bl_note = self.index.notes_by_id.get(bid)
            if bl_note:
                links.append(
                    f'<li><a href="{_note_public_url(bl_note)}" class="internal-link">{escape(bl_note.title)}</a></li>'
                )
        if not links:
            return ""
        return f"""\
<section class="backlinks">
  <h3>Backlinks</h3>
  <ul>{"".join(links)}</ul>
</section>"""

    def _render_toc(self, note: NoteRecord) -> str:
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


def _note_public_url(note: NoteRecord) -> str:
    permalink = note.frontmatter.get("permalink")
    if permalink:
        return "/" + str(permalink).lstrip("/")
    return note.url_path
