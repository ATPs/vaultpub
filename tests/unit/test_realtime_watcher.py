from __future__ import annotations

import asyncio

import pytest

from vaultpub.core.config import PublisherConfig
from vaultpub.core.realtime.events import EventBus
from vaultpub.core.realtime.watcher import (
    DEFAULT_WATCH_RUST_TIMEOUT_MS,
    RealtimeState,
    _classify_changes,
    watch_vault,
)


def test_classify_changes_uses_canonical_attachment_url(tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_text("fake image", encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path)

    event = _classify_changes({("modified", str(image_path))}, tmp_path, config)

    assert len(event.changed) == 1
    assert event.changed[0].kind == "attachment"
    assert event.changed[0].url == "/__assets__/image.png"


def test_classify_changes_marks_navigation_controls_as_nav_changes(tmp_path) -> None:
    control_path = tmp_path / "Folder" / "__order__.json"
    control_path.parent.mkdir()
    control_path.write_text('["A.md"]', encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path)

    event = _classify_changes({("modified", str(control_path))}, tmp_path, config)

    assert event.nav_changed
    assert [(change.kind, change.url) for change in event.changed] == [("navigation", "/Folder/")]


def test_classify_changes_ignores_reserved_dunder_roots(tmp_path) -> None:
    hidden_path = tmp_path / "__slides__" / "Deck.md"
    hidden_path.parent.mkdir()
    hidden_path.write_text("# Deck", encoding="utf-8")

    event = _classify_changes({("modified", str(hidden_path))}, tmp_path, PublisherConfig(vault_path=tmp_path))

    assert not event.changed
    assert not event.deleted


@pytest.mark.asyncio
async def test_watch_vault_passes_stop_event_and_short_rust_timeout(tmp_path, monkeypatch) -> None:
    config = PublisherConfig(vault_path=tmp_path)
    seen: dict[str, object] = {}

    async def fake_awatch(*paths, **kwargs):
        seen["paths"] = paths
        seen["kwargs"] = kwargs
        if False:
            yield set()

    import watchfiles

    monkeypatch.setattr(watchfiles, "awatch", fake_awatch)

    stop_event = asyncio.Event()
    await watch_vault(
        config,
        indexer=None,
        bus=EventBus(),
        state=RealtimeState(index=None, renderer=None),
        stop_event=stop_event,
    )

    assert seen["paths"] == (str(tmp_path.resolve()),)
    assert seen["kwargs"]["stop_event"] is stop_event
    assert seen["kwargs"]["rust_timeout"] == DEFAULT_WATCH_RUST_TIMEOUT_MS
