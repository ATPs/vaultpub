"""Django settings bridge — reads VAULTPUB from settings into PublisherConfig."""
from __future__ import annotations

from pathlib import Path

from django.conf import settings

from vaultpub.core.config import PublisherConfig


def get_publisher_configs() -> dict[str, PublisherConfig]:
    """Return all configured PublisherConfig instances from Django settings."""
    raw = getattr(settings, "VAULTPUB", {})
    if not raw:
        return {}

    configs: dict[str, PublisherConfig] = {}
    for site_key, site_data in raw.items():
        vault_path = Path(site_data.get("vault_path", "."))
        kwargs = {
            "vault_path": vault_path,
            "url_prefix": site_data.get("url_prefix", "/"),
            "home_file": site_data.get("home_file"),
            "show_graph": site_data.get("show_graph", True),
            "show_backlinks": site_data.get("show_backlinks", True),
            "show_search": site_data.get("show_search", True),
            "show_toc": site_data.get("show_toc", True),
            "site_name": site_data.get("site_name", "vaultpub"),
            "site_title": site_data.get("site_title"),
            "site_description": site_data.get("site_description"),
            "site_url": site_data.get("site_url"),
            "show_navigation": site_data.get("show_navigation", True),
            "show_theme_toggle": site_data.get("show_theme_toggle", True),
            "show_hover_preview": site_data.get("show_hover_preview", True),
            "hidden_file_access": site_data.get("hidden_file_access", False),
            "exclude_folders": tuple(site_data.get("exclude_folders", ())),
            "enable_mermaid": site_data.get("enable_mermaid", True),
            "enable_math": site_data.get("enable_math", True),
        }
        configs[site_key] = PublisherConfig(**kwargs)

    return configs


def get_default_config() -> PublisherConfig | None:
    """Get the default PublisherConfig, or None if not configured."""
    configs = get_publisher_configs()
    if not configs:
        return None
    return configs.get("default", next(iter(configs.values())))
