"""HTML rendering pipeline."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import NoteRecord, VaultIndex
from vaultpub.core.parser.callouts import parse_callout_block, render_callout_html
from vaultpub.core.parser.markdown import render_markdown
from vaultpub.core.parser.obsidian_links import (
    find_wikilinks,
    parse_wikilink_target,
    strip_obsidian_comments,
)


class Renderer:
    """Renders notes to HTML using the vault index."""

    def __init__(self, config: PublisherConfig, index: VaultIndex) -> None:
        self.config = config
        self.index = index

    def render_note(self, note: NoteRecord, embed_depth: int = 0) -> str:
        content = note.raw_markdown
        content = strip_obsidian_comments(content)
        content = self._preprocess_wikilinks(content, note)
        content = self._preprocess_callouts(content)

        html = render_markdown(
            content,
            strict_line_breaks=self.config.strict_line_breaks,
            html_safe_mode=self.config.html_safe_mode,
        )
        html = self._add_heading_anchors(html)
        return html

    def _preprocess_wikilinks(self, content: str, source_note: NoteRecord) -> str:
        replacements: list[tuple[int, int, str]] = []

        for start, end, raw_target, is_embed in find_wikilinks(content):
            target_text, anchor, display_text, size = parse_wikilink_target(raw_target)

            # Self-reference
            if target_text == "" and anchor:
                href = f"#{_slugify(anchor.lstrip('^'))}" if not anchor.startswith("^") else f"#^{anchor.lstrip('^')}"
                dtext = display_text or anchor
                replacements.append((start, end, f"[{dtext}]({href})"))
                continue

            notes_by_id = self.index.notes_by_id
            notes_by_path = self.index.notes_by_path
            notes_by_stem = self.index.notes_by_stem
            notes_by_alias = self.index.notes_by_alias

            att_ext = PurePosixPath(target_text).suffix.lstrip(".").lower()
            is_attachment = att_ext in self.config.allowed_attachment_types

            if is_attachment and not is_embed:
                att_url = "/assets/" + target_text
                dtext = display_text or target_text
                replacements.append((start, end, f"[{dtext}]({att_url})"))
                continue

            if is_embed and is_attachment:
                att_url = "/assets/" + target_text
                if att_ext in ("png", "jpg", "jpeg", "gif", "svg", "webp"):
                    size_attr = ""
                    if size:
                        parts = size.split("x")
                        if len(parts) == 1:
                            size_attr = f' width="{parts[0]}"'
                        else:
                            size_attr = f' width="{parts[0]}" height="{parts[1]}"'
                    replacements.append((start, end, f'<img src="{att_url}" alt="{target_text}"{size_attr}>'))
                else:
                    replacements.append((start, end, f'<a href="{att_url}">{display_text or target_text}</a>'))
                continue

            resolved_url = None
            target_clean = target_text if "." in target_text else target_text + ".md"
            if target_clean in notes_by_path:
                resolved_url = notes_by_id[notes_by_path[target_clean]].url_path
            elif target_text in notes_by_path:
                resolved_url = notes_by_id[notes_by_path[target_text]].url_path
            else:
                note_dir = source_note.rel_path.parent
                rel_target = (note_dir / target_text).as_posix()
                if rel_target in notes_by_path:
                    resolved_url = notes_by_id[notes_by_path[rel_target]].url_path
                else:
                    rel_target_md = rel_target + ".md"
                    if rel_target_md in notes_by_path:
                        resolved_url = notes_by_id[notes_by_path[rel_target_md]].url_path
                    else:
                        stem = PurePosixPath(target_text).stem
                        if stem in notes_by_stem:
                            resolved_url = notes_by_id[notes_by_stem[stem][0]].url_path
                        else:
                            alias_key = target_text.lower()
                            if alias_key in notes_by_alias:
                                resolved_url = notes_by_id[notes_by_alias[alias_key][0]].url_path

            if resolved_url:
                if anchor:
                    resolved_url += "#" + _slugify(anchor) if not anchor.startswith("^") else "#^" + anchor.lstrip("^")
                dtext = display_text or target_text
                if is_embed:
                    replacements.append(
                        (start, end, f'<div class="embed-wrapper"><a href="{resolved_url}">{dtext}</a></div>')
                    )
                else:
                    replacements.append((start, end, f"[{dtext}]({resolved_url})"))
            else:
                dtext = display_text or target_text
                resolved_target = raw_target.rsplit("|", 1)[0] if "|" in raw_target else raw_target
                link_html = f'<a class="internal-link is-unresolved" data-target="{resolved_target}">{dtext}</a>'
                replacements.append((start, end, link_html))

        for start, end, repl in reversed(replacements):
            content = content[:start] + repl + content[end:]

        return content

    def _preprocess_callouts(self, content: str) -> str:
        lines = content.split("\n")
        result_lines: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith(">") and "[!" in line:
                callout, next_i = parse_callout_block(lines, i)
                if callout:
                    result_lines.append(render_callout_html(callout))
                    i = next_i
                    continue
            result_lines.append(line)
            i += 1
        return "\n".join(result_lines)

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
                links.append(f'<li><a href="{bl_note.url_path}">{bl_note.title}</a></li>')
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
