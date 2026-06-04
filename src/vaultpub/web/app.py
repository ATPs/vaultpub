"""vaultpub web — standalone ASGI application."""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager, suppress

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.realtime.events import EventBus
from vaultpub.core.realtime.watcher import RealtimeState, watch_vault
from vaultpub.core.render.renderer import Renderer
from vaultpub.web.routes import (
    AppState,
    api_graph,
    api_page,
    api_search,
    attachment,
    index_page,
    page,
    search_index,
)
from vaultpub.web.sse import events_version, sse_endpoint


def create_app(config: PublisherConfig) -> Starlette:
    indexer = VaultIndexer(config)
    vault_index = indexer.build()
    renderer = Renderer(config, vault_index)
    event_bus = EventBus()
    rt_state = RealtimeState(index=vault_index, renderer=renderer)

    state = AppState(
        config=config,
        index=vault_index,
        renderer=renderer,
        indexer=indexer,
        event_bus=event_bus,
        rt_state=rt_state,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette):  # type: ignore[no-untyped-def]
        watcher_task = None
        if config.realtime:
            watcher_task = asyncio.create_task(
                watch_vault(config, indexer, event_bus, rt_state, debounce_ms=config.debounce_ms)
            )
        try:
            yield
        finally:
            if watcher_task:
                watcher_task.cancel()
                with suppress(asyncio.CancelledError):
                    await watcher_task

    frontend_static = os.path.join(os.path.dirname(__file__), "..", "django_app", "static", "vaultpub")

    routes = [
        Route("/", endpoint=index_page, methods=["GET"]),
        Route("/assets/{path:path}", endpoint=attachment, methods=["GET"]),
        Route("/api/page/{path:path}", endpoint=api_page, methods=["GET"]),
        Route("/api/search", endpoint=api_search, methods=["GET"]),
        Route("/search-index.json", endpoint=search_index, methods=["GET"]),
        Route("/api/graph", endpoint=api_graph, methods=["GET"]),
        Route("/graph.json", endpoint=api_graph, methods=["GET"]),
        Route("/api/graph/local/{path:path}", endpoint=api_graph, methods=["GET"]),
        Route("/api/events", endpoint=sse_endpoint, methods=["GET"]),
        Route("/api/events/version", endpoint=events_version, methods=["GET"]),
    ]

    if os.path.isdir(frontend_static):
        routes.append(Mount("/static/vaultpub", app=StaticFiles(directory=frontend_static), name="static"))

    routes.append(Route("/{path:path}", endpoint=page, methods=["GET"]))

    app = Starlette(debug=False, routes=routes, lifespan=lifespan)
    app.state.vaultpub_state = state

    return app
