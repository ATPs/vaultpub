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
    assert event.changed[0].url == "/assets/image.png"


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
