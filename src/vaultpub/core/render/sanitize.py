"""HTML sanitization."""
from __future__ import annotations

import bleach

ALLOWED_TAGS = [
    "a", "abbr", "article", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
    "dd", "del", "details", "div", "dl", "dt", "em", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins",
    "kbd", "li", "mark", "nav", "ol", "p", "pre", "q", "rp", "rt", "ruby",
    "s", "samp", "section", "small", "span", "strong", "sub", "summary", "sup",
    "table", "tbody", "td", "tfoot", "th", "thead", "time", "tr", "u", "ul", "var",
    # Mermaid / math
    "div", "span",
    # Embeds
    "audio", "video", "iframe", "object", "embed",
    "source", "track",
]

ALLOWED_ATTRS: dict[str, list[str]] = {
    "*": [
        "class", "id", "style",
        "data-target", "data-callout", "data-callout-fold", "data-embed-source", "data-note-id", "data-note-path",
    ],
    "a": ["href", "title", "target", "rel", "data-target"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "audio": ["src", "controls", "preload"],
    "video": ["src", "controls", "width", "height", "preload", "poster"],
    "iframe": ["src", "width", "height", "frameborder", "allowfullscreen"],
    "source": ["src", "type"],
    "track": ["src", "kind", "srclang", "label"],
    "time": ["datetime"],
    "col": ["span"],
    "colgroup": ["span"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "ftp"]


def sanitize_html(html: str) -> str:
    """Sanitize HTML, allowing only safe tags and attributes."""
    return bleach.clean(  # type: ignore[no-any-return]
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def add_external_link_attrs(html: str) -> str:
    """Add rel='noopener noreferrer' and target='_blank' to external links."""
    import re

    def _fix_link(match: re.Match) -> str:
        href = match.group(1)
        if href and (href.startswith("http://") or href.startswith("https://")):
            full = match.group(0)
            if "rel=" not in full:
                full = full.replace("<a ", '<a rel="noopener noreferrer" target="_blank" ')
            return full
        return match.group(0)

    return re.sub(r'<a\s[^>]*href="(https?://[^"]*)"[^>]*>', _fix_link, html)
