"""Math block processing helpers."""
from __future__ import annotations


def wrap_math_inline(content: str) -> str:
    """Wrap inline math $...$ in HTML spans for KaTeX."""
    return f'<span class="math inline">{content}</span>'


def wrap_math_block(content: str) -> str:
    """Wrap block math $$...$$ in HTML divs for KaTeX."""
    return f'<div class="math block">{content}</div>'
