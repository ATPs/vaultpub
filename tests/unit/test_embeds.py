"""Tests for embed classification and rendering."""
from __future__ import annotations

from vaultpub.core.parser.embeds import (
    classify_embed_ext,
    render_audio_embed,
    render_image_embed,
    render_pdf_embed,
    render_video_embed,
)


def test_classify_image() -> None:
    assert classify_embed_ext("png") == "image"
    assert classify_embed_ext("jpg") == "image"
    assert classify_embed_ext("svg") == "image"


def test_classify_audio() -> None:
    assert classify_embed_ext("mp3") == "audio"


def test_classify_video() -> None:
    assert classify_embed_ext("mp4") == "video"


def test_classify_pdf() -> None:
    assert classify_embed_ext("pdf") == "pdf"


def test_classify_note() -> None:
    assert classify_embed_ext("md") == "note"
    assert classify_embed_ext("") == "note"


def test_render_image_embed() -> None:
    html = render_image_embed("/assets/img.png", size="300")
    assert 'src="/assets/img.png"' in html
    assert 'width="300"' in html

    html2 = render_image_embed("/assets/img.png", size="300x200")
    assert 'height="200"' in html2


def test_render_audio_embed() -> None:
    html = render_audio_embed("/assets/sound.mp3")
    assert "<audio controls" in html


def test_render_video_embed() -> None:
    html = render_video_embed("/assets/video.mp4")
    assert "<video controls" in html


def test_render_pdf_embed() -> None:
    html = render_pdf_embed("/assets/doc.pdf")
    assert "<iframe" in html
