"""Embed processing (images, notes, audio, video, PDF)."""
from __future__ import annotations


def classify_embed_ext(ext: str) -> str:
    """Classify an embed target by file extension.

    Returns: 'image', 'audio', 'video', 'pdf', 'note', 'canvas', 'unknown'
    """
    ext = ext.lower().lstrip(".")
    if ext in ("png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico"):
        return "image"
    if ext in ("mp3", "wav", "ogg", "flac", "m4a"):
        return "audio"
    if ext in ("mp4", "webm", "mov", "avi"):
        return "video"
    if ext == "pdf":
        return "pdf"
    if ext == "canvas":
        return "canvas"
    if ext in ("md", ""):
        return "note"
    return "unknown"


def render_image_embed(url: str, size: str | None = None, alt: str = "") -> str:
    """Render an image embed to HTML."""
    attrs = f'src="{url}"'
    if alt:
        attrs += f' alt="{alt}"'
    if size:
        parts = size.split("x")
        if len(parts) == 1:
            attrs += f' width="{parts[0]}"'
        else:
            attrs += f' width="{parts[0]}" height="{parts[1]}"'
    return f"<img {attrs}>"


def render_audio_embed(url: str) -> str:
    return f'<audio controls src="{url}"></audio>'


def render_video_embed(url: str) -> str:
    return f'<video controls src="{url}"></video>'


def render_pdf_embed(url: str) -> str:
    return f'<iframe src="{url}" class="pdf-embed"></iframe>'


def render_note_embed(html_content: str) -> str:
    """Wrap embedded note content."""
    return f'<div class="embed-wrapper">{html_content}</div>'


def render_embed_error(message: str) -> str:
    return f'<div class="embed-error">{message}</div>'
