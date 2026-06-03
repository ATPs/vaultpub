"""Mermaid diagram placeholder."""
from __future__ import annotations


def wrap_mermaid(content: str) -> str:
    """Wrap Mermaid diagram content in a div for client-side rendering."""
    return f'<div class="mermaid">{content}</div>'
