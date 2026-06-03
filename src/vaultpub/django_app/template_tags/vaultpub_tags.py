"""Django template tags for vaultpub."""
from __future__ import annotations

from django import template

register = template.Library()


@register.simple_tag
def vaultpub_version() -> str:
    import vaultpub
    return vaultpub.__version__
