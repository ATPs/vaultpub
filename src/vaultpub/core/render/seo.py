"""SEO helpers."""
from __future__ import annotations

from html import escape

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import NoteRecord
from vaultpub.core.paths import file_display_name


def build_page_title(note: NoteRecord, config: PublisherConfig) -> str:
    """Build the <title> for a page."""
    site = config.site_title or config.site_name
    display_name = file_display_name(note.rel_path)
    if display_name:
        return f"{display_name} - {site}"
    return site


def build_page_description(note: NoteRecord, config: PublisherConfig) -> str:
    """Build meta description for a page."""
    desc = note.frontmatter.get("description")
    if desc:
        return str(desc)
    return note.excerpt[:200]


def build_meta_tags(note: NoteRecord, config: PublisherConfig) -> str:
    """Build meta tags for SEO/OpenGraph/Twitter."""
    title = build_page_title(note, config)
    desc = build_page_description(note, config)
    url = config.site_url or ""
    public_path = _note_public_url(note)
    page_url = f"{url.rstrip('/')}{public_path}" if url else ""
    title_text = escape(title)
    title_attr = escape(title, quote=True)
    desc_attr = escape(desc, quote=True)
    site_type_attr = escape(config.site_type, quote=True)

    tags = [
        f"<title>{title_text}</title>",
        f'<meta name="description" content="{desc_attr}">',
    ]
    if page_url:
        page_url_attr = escape(page_url, quote=True)
        tags.append(f'<link rel="canonical" href="{page_url_attr}">')
        tags.append(f'<meta property="og:url" content="{page_url_attr}">')

    tags.extend([
        f'<meta property="og:type" content="{site_type_attr}">',
        f'<meta property="og:title" content="{title_attr}">',
        f'<meta property="og:description" content="{desc_attr}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])

    image = note.frontmatter.get("image") or config.site_image
    if image:
        img_url = image if image.startswith("http") else f"{url.rstrip('/')}/{image.lstrip('/')}"
        tags.append(f'<meta property="og:image" content="{escape(img_url, quote=True)}">')

    return "\n".join(tags)


def _note_public_url(note: NoteRecord) -> str:
    return note.url_path
