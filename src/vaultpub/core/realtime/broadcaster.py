"""SSE broadcaster that pushes events to connected clients."""
from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncGenerator, Awaitable, Callable

from vaultpub.core.realtime.events import EventBus, IndexChangedEvent

SSE_PING_INTERVAL_SECONDS = 15.0
SSE_SHUTDOWN_POLL_INTERVAL_SECONDS = 0.5


class SSEBroadcaster:
    """Manages SSE connections and broadcasts index change events."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    async def stream(
        self,
        is_disconnected: Callable[[], Awaitable[bool]],
        shutdown_signal: threading.Event | None = None,
    ) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE event strings."""
        queue = self.bus.subscribe()
        idle_seconds = 0.0
        try:
            yield _sse_message({"type": "connected", "version": self.bus.version})

            while True:
                if shutdown_signal is not None and shutdown_signal.is_set():
                    break
                try:
                    event: IndexChangedEvent = await asyncio.wait_for(
                        queue.get(),
                        timeout=SSE_SHUTDOWN_POLL_INTERVAL_SECONDS,
                    )
                    idle_seconds = 0.0
                    yield _sse_message(_event_to_dict(event))
                except TimeoutError:
                    idle_seconds += SSE_SHUTDOWN_POLL_INTERVAL_SECONDS
                    if idle_seconds >= SSE_PING_INTERVAL_SECONDS:
                        idle_seconds = 0.0
                        yield _sse_message({"type": "ping"})

                if await is_disconnected():
                    break
        finally:
            self.bus.unsubscribe(queue)


def _event_to_dict(event: IndexChangedEvent) -> dict:
    return {
        "type": "index.changed",
        "version": event.version,
        "changed": [
            {"kind": c.kind, "path": c.path, "url": c.url, "change": c.change}
            for c in event.changed
        ],
        "deleted": [
            {"kind": c.kind, "path": c.path, "url": c.url, "change": c.change}
            for c in event.deleted
        ],
        "graph_changed": event.graph_changed,
        "nav_changed": event.nav_changed,
        "search_changed": event.search_changed,
    }


def _sse_message(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
