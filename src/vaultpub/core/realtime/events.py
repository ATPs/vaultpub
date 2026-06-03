"""Event bus for index change notifications."""
from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass, field


@dataclass
class ChangeRecord:
    kind: str  # "note" | "attachment"
    path: str
    url: str
    change: str  # "modified" | "created" | "deleted"


@dataclass
class IndexChangedEvent:
    version: int = 0
    changed: list[ChangeRecord] = field(default_factory=list)
    deleted: list[ChangeRecord] = field(default_factory=list)
    graph_changed: bool = False
    nav_changed: bool = False
    search_changed: bool = False
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Simple in-process pub/sub for index change events."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[IndexChangedEvent]] = []
        self._version = 0
        self._history: list[IndexChangedEvent] = []

    @property
    def version(self) -> int:
        return self._version

    async def publish(self, event: IndexChangedEvent) -> None:
        self._version += 1
        event.version = self._version
        event.timestamp = time.time()
        self._history.append(event)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        dead: list[asyncio.Queue[IndexChangedEvent]] = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue[IndexChangedEvent]:
        q: asyncio.Queue[IndexChangedEvent] = asyncio.Queue(maxsize=256)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, queue: asyncio.Queue[IndexChangedEvent]) -> None:
        with contextlib.suppress(ValueError):
            self._subscribers.remove(queue)

    def get_events_since(self, version: int) -> list[IndexChangedEvent]:
        return [e for e in self._history if e.version > version]
