from __future__ import annotations

import asyncio
import threading

import pytest

from vaultpub.core.realtime.broadcaster import SSEBroadcaster
from vaultpub.core.realtime.events import EventBus


@pytest.mark.asyncio
async def test_sse_broadcaster_stops_promptly_on_shutdown_signal() -> None:
    bus = EventBus()
    broadcaster = SSEBroadcaster(bus)
    shutdown_signal = threading.Event()

    async def never_disconnected() -> bool:
        return False

    stream = broadcaster.stream(never_disconnected, shutdown_signal=shutdown_signal)

    connected = await anext(stream)
    assert '"type": "connected"' in connected

    shutdown_signal.set()

    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(anext(stream), timeout=1.0)
