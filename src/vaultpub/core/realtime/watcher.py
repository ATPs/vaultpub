"""File watcher using watchfiles for realtime index updates."""
from __future__ import annotations

import asyncio
import os

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.paths import normalize_rel_path, rel_path_to_url_path
from vaultpub.core.realtime.events import ChangeRecord, EventBus, IndexChangedEvent

SKIP_PATTERNS = (".swp", ".swx", "~", ".tmp", ".DS_Store", ".swp", ".swo")
SKIP_DIRS = (".obsidian", ".git", ".trash")


async def watch_vault(
    config: PublisherConfig,
    indexer: VaultIndexer,
    bus: EventBus,
    debounce_ms: int = 150,
) -> None:
    """Watch vault for file changes and emit index update events."""
    try:
        from watchfiles import awatch
    except ImportError:
        return

    root = config.vault_path.resolve()

    async for changes in awatch(str(root)):
        affected = _classify_changes(changes, root, config)
        if not affected.changed and not affected.deleted:
            continue

        # Debounce
        await asyncio.sleep(debounce_ms / 1000.0)

        # Rebuild affected parts of the index
        try:
            await _apply_changes(indexer, affected, config)
        except Exception:
            continue

        await bus.publish(affected)


def _classify_changes(
    raw_changes: set[tuple[int, str]],
    root: os.PathLike[str],
    config: PublisherConfig,
) -> IndexChangedEvent:
    event = IndexChangedEvent()

    for change_type, path_str in raw_changes:
        try:
            rel = normalize_rel_path(os.PathLike(path_str), os.PathLike(str(root)))
        except Exception:
            continue

        # Skip hidden and excluded
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        if any(d in rel.split("/") for d in config.exclude_folders):
            continue
        if any(path_str.endswith(p) for p in SKIP_PATTERNS):
            continue

        ext = os.path.splitext(path_str)[1].lower()

        if ext == ".md":
            url = rel_path_to_url_path(rel)
            rec = ChangeRecord(
                kind="note",
                path=rel,
                url=url,
                change={1: "modified", 2: "created", 3: "deleted"}.get(change_type, "modified"),
            )
            if change_type == 3:  # deleted
                event.deleted.append(rec)
                event.nav_changed = True
                event.search_changed = True
                event.graph_changed = True
            else:
                event.changed.append(rec)
                event.search_changed = True
                event.graph_changed = True
        elif ext.lstrip(".") in config.allowed_attachment_types:
            rec = ChangeRecord(
                kind="attachment",
                path=rel,
                url="/assets/" + rel,
                change={1: "modified", 2: "created", 3: "deleted"}.get(change_type, "modified"),
            )
            event.changed.append(rec)

    return event


async def _apply_changes(
    indexer: VaultIndexer,
    event: IndexChangedEvent,
    config: PublisherConfig,
) -> None:
    """Rebuild the index incrementally. For simplicity, do a full rebuild on any change."""
    # Full rebuild for correctness (optimize later for performance targets)
    indexer.build()
    # The index is updated in-place via the rebuild
