"""File watcher using watchfiles for realtime index updates."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.paths import normalize_rel_path, rel_path_to_url_path
from vaultpub.core.realtime.events import ChangeRecord, EventBus, IndexChangedEvent
from vaultpub.core.security import is_force_included, is_text_file, infer_language

SKIP_PATTERNS = (".swp", ".swx", "~", ".tmp", ".DS_Store", ".swo")


@dataclass
class RealtimeState:
    """Mutable state container that can be replaced atomically after rebuild."""

    index: object  # VaultIndex
    renderer: object  # Renderer


async def watch_vault(
    config: PublisherConfig,
    indexer: VaultIndexer,
    bus: EventBus,
    state: RealtimeState,
    debounce_ms: int = 150,
) -> None:
    """Watch vault for file changes and emit index update events."""
    try:
        from watchfiles import awatch
    except ImportError:
        return

    root = config.vault_path.resolve()

    async for changes in awatch(str(root)):
        event = _classify_changes(changes, root, config)
        if not event.changed and not event.deleted:
            continue

        # Debounce: wait for a quiet period
        await asyncio.sleep(debounce_ms / 1000.0)

        # Rebuild index and update state atomically
        try:
            new_index = indexer.build()
            from vaultpub.core.render.renderer import Renderer

            new_renderer = Renderer(config, new_index)
            state.index = new_index
            state.renderer = new_renderer
        except Exception:
            continue

        await bus.publish(event)


_CHANGE_MAP: dict[Any, str] = {}


def _get_change_map() -> dict[Any, str]:
    if not _CHANGE_MAP:
        try:
            from watchfiles import Change
        except ImportError:
            return {}
        _CHANGE_MAP.update({
            Change.added: "created",
            Change.modified: "modified",
            Change.deleted: "deleted",
        })
    return _CHANGE_MAP


def _classify_changes(
    raw_changes: set[tuple[Any, str]],
    root: Path,
    config: PublisherConfig,
) -> IndexChangedEvent:
    event = IndexChangedEvent()
    change_map = _get_change_map()
    compiled_exclude = getattr(config, "_compiled_force_exclude", [])

    for change_type, path_str in raw_changes:
        change_name = change_map.get(change_type, "modified")
        fpath = Path(path_str)

        # Skip temp/swap files
        if any(str(fpath).endswith(p) for p in SKIP_PATTERNS):
            continue

        try:
            rel = normalize_rel_path(fpath, root)
        except Exception:
            continue

        # Skip hidden directories/files
        parts = rel.split("/")
        if any(part.startswith(".") for part in parts):
            continue

        # Skip excluded folders
        if any(d in parts for d in config.exclude_folders):
            continue

        # Skip force-excluded paths
        if compiled_exclude and any(pat.search(rel) for pat in compiled_exclude):
            continue

        ext = fpath.suffix.lower()

        if ext == ".md":
            url = rel_path_to_url_path(rel)
            rec = ChangeRecord(
                kind="note",
                path=rel,
                url=url,
                change=change_name,
            )
            if change_name == "deleted":
                event.deleted.append(rec)
                event.nav_changed = True
                event.search_changed = True
                event.graph_changed = True
            else:
                event.changed.append(rec)
                event.search_changed = True
                event.graph_changed = True
        elif is_force_included(rel, config) and fpath.exists() and is_text_file(fpath):
            rec = ChangeRecord(
                kind="textpage",
                path=rel,
                url="/" + rel,
                change=change_name,
            )
            if change_name == "deleted":
                event.deleted.append(rec)
                event.nav_changed = True
                event.search_changed = True
            else:
                event.changed.append(rec)
                event.search_changed = True
        elif ext.lstrip(".") in config.allowed_attachment_types:
            rec = ChangeRecord(
                kind="attachment",
                path=rel,
                url="/assets/" + rel,
                change=change_name,
            )
            event.changed.append(rec)

    return event
