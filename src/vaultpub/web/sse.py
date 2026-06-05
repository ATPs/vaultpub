"""SSE (Server-Sent Events) endpoint for realtime updates."""
from __future__ import annotations

import asyncio
import json

from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse

from vaultpub.core.realtime.broadcaster import (
    SSE_PING_INTERVAL_SECONDS,
    SSE_SHUTDOWN_POLL_INTERVAL_SECONDS,
    SSEBroadcaster,
)


async def sse_endpoint(request: Request) -> StreamingResponse:
    """SSE endpoint that streams index change events to clients."""
    state = request.app.state.vaultpub_state
    bus = getattr(state, "event_bus", None)
    shutdown_signal = getattr(state, "shutdown_signal", None)

    if bus is None:
        async def ping_stream():  # type: ignore[no-untyped-def]
            idle_seconds = 0.0
            while True:
                if shutdown_signal is not None and shutdown_signal.is_set():
                    break
                if await request.is_disconnected():
                    break
                if idle_seconds >= SSE_PING_INTERVAL_SECONDS:
                    idle_seconds = 0.0
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                await asyncio.sleep(SSE_SHUTDOWN_POLL_INTERVAL_SECONDS)
                idle_seconds += SSE_SHUTDOWN_POLL_INTERVAL_SECONDS

        return StreamingResponse(
            ping_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    broadcaster = SSEBroadcaster(bus)

    async def event_stream():  # type: ignore[no-untyped-def]
        async for msg in broadcaster.stream(request.is_disconnected, shutdown_signal=shutdown_signal):
            yield msg

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def events_version(request: Request) -> JSONResponse:
    """Return the current EventBus version for polling clients."""
    state = request.app.state.vaultpub_state
    bus = getattr(state, "event_bus", None)
    version = bus.version if bus else 0
    return JSONResponse({"version": version})
