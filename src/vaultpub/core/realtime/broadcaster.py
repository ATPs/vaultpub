"""SSE broadcaster that pushes events to connected clients."""
from __future__ import annotations

import asyncio
import json

from vaultpub.core.realtime.events import EventBus, IndexChangedEvent


class SSEBroadcaster:
    """Manages SSE connections and broadcasts index change events."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    async def stream(self, request_disconnected: callable) -> str:
        """Async generator yielding SSE event strings."""
        queue = self.bus.subscribe()
        try:
            # Send initial version
            yield _sse_message({"type": "connected", "version": self.bus.version})

            while True:
                try:
                    event: IndexChangedEvent = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield _sse_message({
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
                    })
                except TimeoutError:
                    # Send ping to keep connection alive
                    yield _sse_message({"type": "ping"})

                if request_disconnected():
                    break
        finally:
            self.bus.unsubscribe(queue)


def _sse_message(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
