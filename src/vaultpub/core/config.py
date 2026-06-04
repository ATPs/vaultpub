from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from vaultpub.core.exceptions import ConfigError

ThemeMode = Literal["light", "dark", "system"]
UrlStyle = Literal["path", "publish", "slug"]
PublishMode = Literal["all", "publish_true", "publish_false_hides"]
RealtimeTransport = Literal["auto", "sse", "websocket", "poll"]


@dataclass(frozen=True)
class PublisherConfig:
    vault_path: Path

    site_name: str = "vaultpub"
    site_title: str | None = None
    site_description: str | None = None
    site_url: str | None = None
    site_logo: str | None = None
    site_image: str | None = None
    site_type: str = "article"

    url_prefix: str = "/"
    url_style: UrlStyle = "path"
    home_file: str | None = None
    default_home_candidates: tuple[str, ...] = ("README", "index", "Home")

    include_folders: tuple[str, ...] = ()
    exclude_folders: tuple[str, ...] = (".obsidian", ".git", ".trash", "private", "trash")
    exclude_globs: tuple[str, ...] = ()
    force_include_regexes: tuple[str, ...] = ()
    force_exclude_regexes: tuple[str, ...] = ()
    publish_property_mode: PublishMode = "publish_false_hides"

    hidden_file_access: bool = False
    follow_symlinks: bool = False
    allowed_attachment_types: tuple[str, ...] = (
        "png", "jpg", "jpeg", "gif", "svg", "webp",
        "pdf", "mp3", "wav", "ogg", "mp4", "webm",
    )
    max_markdown_size_bytes: int = 2_000_000
    max_attachment_size_bytes: int | None = None

    strict_line_breaks: bool = True
    readable_line_length: bool = True
    hide_title: bool = False
    show_inline_title: bool = True
    collapse_metadata: bool = True
    html_safe_mode: bool = True
    allow_raw_html: bool = False

    show_navigation: bool = True
    show_search: bool = True
    show_graph: bool = True
    show_local_graph: bool = True
    show_toc: bool = True
    show_backlinks: bool = True
    show_unlinked_mentions: bool = False
    show_hover_preview: bool = True
    show_theme_toggle: bool = True
    stacked_pages: bool = False

    default_theme: ThemeMode = "system"
    font_size: int = 16

    enable_mermaid: bool = True
    enable_math: bool = True
    enable_callouts: bool = True
    enable_dataview_placeholder: bool = True

    realtime: bool = True
    realtime_transport: RealtimeTransport = "auto"
    debounce_ms: int = 150

    nav_order: tuple[str, ...] = ()
    nav_hidden: tuple[str, ...] = ()

    analytics_html: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.vault_path, Path):
            object.__setattr__(self, "vault_path", Path(self.vault_path).expanduser().resolve())  # type: ignore[unreachable]
        if self.max_attachment_size_bytes is not None and self.max_attachment_size_bytes <= 0:
            object.__setattr__(self, "max_attachment_size_bytes", None)  # type: ignore[unreachable]

        compiled_include = _compile_regexes(self.force_include_regexes, "force_include_regexes")
        object.__setattr__(self, "_compiled_force_include", compiled_include)

        compiled_exclude = _compile_regexes(self.force_exclude_regexes, "force_exclude_regexes")
        object.__setattr__(self, "_compiled_force_exclude", compiled_exclude)


def load_config_from_yaml(yaml_path: Path) -> dict:
    """Load configuration from a YAML file, returning a dict of PublisherConfig kwargs."""
    import yaml

    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}

    kwargs: dict = {}

    if "vault_path" in data:
        kwargs["vault_path"] = Path(data["vault_path"])

    # site section
    site = data.get("site", {})
    if isinstance(site, dict):
        for key in ("name", "title", "description", "url", "logo", "image", "type"):
            val = site.get(key)
            if val is not None:
                config_key = f"site_{key}"
                kwargs[config_key] = val

    # routing section
    routing = data.get("routing", {})
    if isinstance(routing, dict):
        if "prefix" in routing:
            kwargs["url_prefix"] = routing["prefix"]
        if "home_file" in routing:
            kwargs["home_file"] = routing["home_file"]
        if "url_style" in routing:
            kwargs["url_style"] = routing["url_style"]

    # publish section
    publish = data.get("publish", {})
    if isinstance(publish, dict):
        if "mode" in publish:
            kwargs["publish_property_mode"] = publish["mode"]
        if "include_folders" in publish:
            kwargs["include_folders"] = tuple(publish["include_folders"])
        if "exclude_folders" in publish:
            kwargs["exclude_folders"] = tuple(publish["exclude_folders"])
        if "exclude_globs" in publish:
            kwargs["exclude_globs"] = tuple(publish["exclude_globs"])
        if "force_include_regexes" in publish:
            kwargs["force_include_regexes"] = tuple(publish["force_include_regexes"])
        if "force_exclude_regexes" in publish:
            kwargs["force_exclude_regexes"] = tuple(publish["force_exclude_regexes"])

    # rendering section
    rendering = data.get("rendering", {})
    if isinstance(rendering, dict):
        for key in (
            "strict_line_breaks", "readable_line_length", "hide_title",
            "html_safe_mode", "allow_raw_html", "enable_mermaid",
            "enable_math", "enable_callouts",
        ):
            if key in rendering:
                kwargs[key] = rendering[key]

    # features section
    features = data.get("features", {})
    if isinstance(features, dict):
        for key in (
            "navigation", "search", "graph", "local_graph", "toc",
            "backlinks", "unlinked_mentions", "hover_preview",
            "theme_toggle", "stacked_pages",
        ):
            if key in features:
                kwargs[f"show_{key}"] = features[key]

    # realtime section
    realtime = data.get("realtime", {})
    if isinstance(realtime, dict):
        if "enabled" in realtime:
            kwargs["realtime"] = realtime["enabled"]
        if "transport" in realtime:
            kwargs["realtime_transport"] = realtime["transport"]
        if "debounce_ms" in realtime:
            kwargs["debounce_ms"] = realtime["debounce_ms"]

    return kwargs


_ENV_MAP = {
    "NOTES_PATH": "vault_path",
    "HIDE_FOLDERS": "exclude_folders",
    "HIDDEN_FILE_ACCESS": "hidden_file_access",
    "LINE_BREAKS": "strict_line_breaks",
    "ALLOWED_FILE_LINK_TYPES": "allowed_attachment_types",
    "DISABLE_POP_HOVER": "show_hover_preview",
    "SHOW_TOC": "show_toc",
    "SHOW_LOCAL_GRAPH": "show_local_graph",
    "HOME_FILE": "home_file",
    "FONT_SIZE": "font_size",
    "HTML_SAFE_MODE": "html_safe_mode",
    "SITE_TITLE": "site_title",
    "SITE_TYPE": "site_type",
    "SITE_URL": "site_url",
    "SITE_IMAGE": "site_image",
    "SITE_DESC": "site_description",
    "SITE_NAME": "site_name",
    "SITE_LOGO": "site_logo",
}

_BOOL_ENV_VARS = {
    "HIDDEN_FILE_ACCESS", "LINE_BREAKS", "HTML_SAFE_MODE",
    "SHOW_TOC", "SHOW_LOCAL_GRAPH",
}

_LIST_ENV_VARS = {"HIDE_FOLDERS", "ALLOWED_FILE_LINK_TYPES"}

_INVERT_ENV_VARS = {"DISABLE_POP_HOVER"}


def _config_fields(config: PublisherConfig) -> dict[str, object]:
    """Return only the declared dataclass fields from a config (excludes compiled internals)."""
    return {f.name: getattr(config, f.name) for f in type(config).__dataclass_fields__.values()}  # type: ignore[arg-type]


def apply_env_overrides(config: PublisherConfig) -> PublisherConfig:
    """Apply environment variable overrides to an existing config, returning a new one."""
    kwargs: dict = {f.name: getattr(config, f.name) for f in type(config).__dataclass_fields__.values()}  # type: ignore[arg-type]

    for env_var, config_key in _ENV_MAP.items():
        val = os.environ.get(env_var)
        if val is None or val == "":
            continue
        if env_var in _BOOL_ENV_VARS:
            kwargs[config_key] = val.lower() in ("1", "true", "yes")
        elif env_var in _LIST_ENV_VARS:
            kwargs[config_key] = tuple(v.strip() for v in val.split(",") if v.strip())
        elif env_var in _INVERT_ENV_VARS:
            kwargs[config_key] = val.lower() not in ("1", "true", "yes")
        elif env_var == "FONT_SIZE":
            kwargs[config_key] = int(val)
        elif env_var == "NOTES_PATH":
            kwargs[config_key] = Path(val)
        else:
            kwargs[config_key] = val

    return PublisherConfig(**kwargs)


def load_config(
    vault_path: Path | str | None = None,
    yaml_path: Path | str | None = None,
    **overrides: object,
) -> PublisherConfig:
    """Load PublisherConfig from YAML, env, and overrides.

    Priority: overrides > env > YAML
    """
    yaml_kwargs: dict = {}

    if yaml_path is not None:
        yaml_kwargs = load_config_from_yaml(Path(yaml_path))
    else:
        for candidate in (".vaultpub.yml", ".obsidian-publish.yml"):
            if Path(candidate).exists():
                yaml_kwargs = load_config_from_yaml(Path(candidate))
                break

    if vault_path is not None:
        yaml_kwargs["vault_path"] = vault_path if isinstance(vault_path, Path) else Path(vault_path)
    elif "vault_path" not in yaml_kwargs:
        raise ConfigError("vault_path is required (set via arg, YAML, or NOTES_PATH env)")

    config = PublisherConfig(**yaml_kwargs)
    config = apply_env_overrides(config)

    if overrides:
        current = {f.name: getattr(config, f.name) for f in type(config).__dataclass_fields__.values()}  # type: ignore[arg-type]
        current.update(overrides)
        config = PublisherConfig(**current)

    return config


def _compile_regexes(patterns: tuple[str, ...], field_name: str) -> list[re.Pattern[str]]:
    """Compile and validate regex patterns. Raises ConfigError on invalid patterns."""
    compiled: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except re.error as e:
            raise ConfigError(f"Invalid regex in {field_name}: {p!r} — {e}") from e
    return compiled
