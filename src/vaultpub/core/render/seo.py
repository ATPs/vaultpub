"""SEO helpers."""
from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.models import NoteRecord


def build_page_title(note: NoteRecord, config: PublisherConfig) -> str:
    """Build the <title> for a page."""
    site = config.site_title or config.site_name
    if note.title:
        return f"{note.title} - {site}"
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
    page_url = f"{url.rstrip('/')}{note.url_path}" if url else ""

    tags = [
        f"<title>{title}</title>",
        f'<meta name="description" content="{desc}">',
    ]
    if page_url:
        tags.append(f'<link rel="canonical" href="{page_url}">')
        tags.append(f'<meta property="og:url" content="{page_url}">')

    tags.extend([
        f'<meta property="og:type" content="{config.site_type}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])

    image = note.frontmatter.get("image") or config.site_image
    if image:
        img_url = image if image.startswith("http") else f"{url.rstrip('/')}/{image.lstrip('/')}"
        tags.append(f'<meta property="og:image" content="{img_url}">')

    return "\n".join(tags)
