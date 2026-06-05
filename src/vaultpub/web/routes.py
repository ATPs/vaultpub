"""Web routes for the standalone ASGI app."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import PurePosixPath

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from vaultpub.core.attachments import attachment_content_disposition, is_download_only_attachment
from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NavNode, NoteRecord, TextPageRecord, VaultIndex
from vaultpub.core.paths import safe_join
from vaultpub.core.render.renderer import Renderer
from vaultpub.core.render.seo import build_meta_tags
from vaultpub.core.render.templates import (
    base_page_template,
    directory_page_html,
    directory_preview_map,
    directory_sibling_files_html,
    find_nav_directory,
    graph_container_html,
    nav_tree_html,
    sidebar_graph_state,
    topbar_context_html_for_directory,
    topbar_context_html_for_note,
    topbar_context_html_for_text_page,
)
from vaultpub.core.security import is_path_excluded, is_path_public


@dataclass
class AppState:
    config: PublisherConfig
    index: VaultIndex
    renderer: Renderer
    indexer: VaultIndexer
    event_bus: object | None = None
    rt_state: object | None = None


def _get_state(request: Request) -> AppState:
    state: AppState = request.app.state.vaultpub_state
    # Use live index from realtime state if available
    rt = state.rt_state
    if rt is not None:
        live_index = getattr(rt, "index", None)
        live_renderer = getattr(rt, "renderer", None)
        if live_index is not None:
            state.index = live_index
        if live_renderer is not None:
            state.renderer = live_renderer
    return state


def _note_public_url(note: NoteRecord) -> str:
    return note.url_path


def _build_url_maps(index: VaultIndex) -> tuple[dict[str, NoteRecord], dict[str, NoteRecord]]:
    canonical_to_note: dict[str, NoteRecord] = {}

    for note in index.notes_by_id.values():
        canonical = _note_public_url(note)
        canonical_to_note[canonical] = note
    return canonical_to_note, canonical_to_note


async def index_page(request: Request) -> HTMLResponse:
    state = _get_state(request)
    home_note = state.indexer.scanner.resolve_home(list(state.index.notes_by_id.values()))
    if home_note is None:
        return HTMLResponse("<h1>No notes found</h1>", status_code=404)
    return _render_note_page(request, home_note)


async def page(request: Request) -> HTMLResponse:
    state = _get_state(request)
    path = request.path_params.get("path", "")
    rel_path = "/" + path

    url_to_note, all_urls_to_note = _build_url_maps(state.index)

    if path.endswith("/"):
        directory = _resolve_directory(state.index.nav_tree, path)
        if directory is not None and directory.path not in ("", "."):
            return _render_directory_page(request, directory)
        return HTMLResponse("Not found", status_code=404)

    # Check note pages first
    if rel_path in url_to_note:
        note = url_to_note[rel_path]
        if not is_path_public(note.rel_path.as_posix(), state.config):
            return HTMLResponse("Not found", status_code=404)
        return _render_note_page(request, note)

    # Check text pages
    tp = state.index.text_pages_by_path.get(path)
    if tp is not None:
        if is_path_excluded(tp.rel_path.as_posix(), state.config):
            return HTMLResponse("Not found", status_code=404)
        return _render_text_page(request, tp)

    return HTMLResponse("Not found", status_code=404)


async def attachment(request: Request) -> Response:
    state = _get_state(request)
    path = request.path_params.get("path", "")

    att = state.index.attachments_by_path.get(path)
    if att is None:
        return HTMLResponse("Not found", status_code=404)

    if is_path_excluded(path, state.config):
        return HTMLResponse("Not found", status_code=404)

    fpath = safe_join(state.config.vault_path, path)
    if not fpath.exists():
        return HTMLResponse("Not found", status_code=404)

    content = fpath.read_bytes()
    headers: dict[str, str] = {}
    if is_download_only_attachment(att.rel_path):
        headers["Content-Disposition"] = attachment_content_disposition(att.rel_path)
    return Response(content, media_type=att.mime_type, headers=headers)


async def api_page(request: Request) -> JSONResponse:
    state = _get_state(request)
    path = request.path_params.get("path", "")
    rel_path = "/" + path

    _canonical_to_note, all_urls_to_note = _build_url_maps(state.index)
    note = all_urls_to_note.get(rel_path)
    if note:
        html = state.renderer.render_note(note)
        return JSONResponse({
            "id": note.id,
            "title": note.rel_path.name,
            "url": _note_public_url(note),
            "html": html,
            "tags": list(note.tags),
            "headings": [{"level": h.level, "text": h.text, "slug": h.slug} for h in note.headings],
            "backlinks": list(note.backlinks),
        })

    # Check text pages
    tp = state.index.text_pages_by_path.get(path)
    if tp is not None:
        code_html = _render_text_page_content(tp)
        return JSONResponse({
            "id": tp.id,
            "title": tp.title,
            "url": tp.url_path,
            "html": code_html,
            "tags": [],
            "headings": [],
            "backlinks": [],
        })

    return JSONResponse({"error": "Not found"}, status_code=404)


async def api_search(request: Request) -> JSONResponse:
    state = _get_state(request)
    q = request.query_params.get("q", "").strip()
    if not q:
        return JSONResponse({"results": []})

    q_lower = q.lower()
    results: list[dict] = []
    for doc in state.index.search_documents:
        title = str(doc.get("title", ""))
        content = str(doc.get("content", ""))
        tags: list[str] = doc.get("tags", [])  # type: ignore[assignment]
        aliases: list[str] = doc.get("aliases", [])  # type: ignore[assignment]

        if (q_lower in title.lower() or
            q_lower in content.lower() or
            any(q_lower in str(t).lower() for t in tags) or
            any(q_lower in str(a).lower() for a in aliases)):
            results.append({
                "title": doc["title"],
                "url": doc["url"],
                "excerpt": doc["excerpt"],
                "tags": list(tags),
            })
            if len(results) >= 20:
                break

    return JSONResponse({"results": results})


async def search_index(request: Request) -> JSONResponse:
    state = _get_state(request)
    return JSONResponse(state.index.search_documents)


async def api_graph(request: Request) -> JSONResponse:
    state = _get_state(request)
    graph = state.index.graph
    path = request.path_params.get("path")

    if path:
        note_id = None
        _canonical_to_note, all_urls_to_note = _build_url_maps(state.index)
        note = all_urls_to_note.get("/" + path)
        if note:
            note_id = note.id
        if note_id:
            nid = f"note:{note_id}"
            local_edges = [e for e in graph.edges if e.source == nid or e.target == nid]
            local_ids = {e.source for e in local_edges} | {e.target for e in local_edges}
            local_nodes = [n for n in graph.nodes if n.id in local_ids]
            return JSONResponse({
                "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in local_nodes],
                "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in local_edges],
            })

    return JSONResponse({
        "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in graph.nodes],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in graph.edges],
    })


def _render_note_page(request: Request, note: NoteRecord) -> HTMLResponse:
    state = _get_state(request)
    body_html = state.renderer.render_article_html(note)
    toc_html = state.renderer.render_toc_html(note) if state.config.show_toc else ""
    backlinks_html = state.renderer.render_backlinks_html(note) if state.config.show_backlinks else ""
    sidebar_right_html = toc_html + backlinks_html
    show_graph, graph_note_id = sidebar_graph_state(state.config, state.index.graph, note)
    graph_html = graph_container_html(show_graph, graph_note_id)
    nav_html = ""
    if state.index.nav_tree:
        nav_html = "<ul>" + nav_tree_html(state.index.nav_tree) + "</ul>"
    head = build_meta_tags(note, state.config)
    topbar_context_html = topbar_context_html_for_note(note)
    page_str = base_page_template(
        body_html,
        nav_html,
        head,
        state.config,
        sidebar_right_html,
        graph_html=graph_html,
        topbar_context_html=topbar_context_html,
    )
    return HTMLResponse(page_str)


def _render_directory_page(request: Request, directory: NavNode) -> HTMLResponse:
    state = _get_state(request)
    body_html = directory_page_html(
        directory,
        current_path=directory.url,
        content_previews=directory_preview_map(
            state.index.notes_by_id.values(),
            state.index.text_pages_by_path.values(),
        ),
    )
    sidebar_right_html = directory_sibling_files_html(state.index.nav_tree, directory)
    nav_html = ""
    if state.index.nav_tree:
        nav_html = "<ul>" + nav_tree_html(state.index.nav_tree) + "</ul>"
    show_graph, graph_note_id = sidebar_graph_state(state.config, state.index.graph, None)
    graph_html = graph_container_html(show_graph, graph_note_id)
    title = "Home" if directory.path in ("", ".") else f"{directory.label}/"
    head = f"<title>{escape(title)} - {escape(state.config.site_name)}</title>"
    topbar_context_html = topbar_context_html_for_directory(
        PurePosixPath(directory.path),
        current_url=directory.url,
    )
    page_str = base_page_template(
        body_html,
        nav_html,
        head,
        state.config,
        sidebar_right_html,
        sidebar_right_title="Directory",
        graph_html=graph_html,
        topbar_context_html=topbar_context_html,
    )
    return HTMLResponse(page_str)


def _render_text_page(request: Request, tp: TextPageRecord) -> HTMLResponse:
    state = _get_state(request)
    body_html = _render_text_page_content(tp)
    nav_html = ""
    if state.index.nav_tree:
        nav_html = "<ul>" + nav_tree_html(state.index.nav_tree) + "</ul>"

    # Minimal meta tags for text pages
    head = f"<title>{escape(tp.title)} - {escape(state.config.site_name)}</title>"
    topbar_context_html = topbar_context_html_for_text_page(tp)
    page_str = base_page_template(
        body_html,
        nav_html,
        head,
        state.config,
        "",
        graph_html="",
        topbar_context_html=topbar_context_html,
    )
    return HTMLResponse(page_str)


def _render_text_page_content(tp: TextPageRecord, current_path: str | None = None) -> str:
    lang_class = f"language-{tp.language}" if tp.language else ""
    page_path = escape(current_path or tp.url_path, quote=True)
    return f"""\
<article class="text-page" data-page-id="{tp.id}" data-page-path="{page_path}" data-current-path="{page_path}">
  <h1>{escape(tp.title)}</h1>
  <div class="code-block">
    <pre><code class="{lang_class}">{escape(tp.raw_text)}</code></pre>
  </div>
</article>"""


def _resolve_directory(nav_tree: NavNode | None, request_path: str) -> NavNode | None:
    if nav_tree is None:
        return None
    return find_nav_directory(nav_tree, request_path.rstrip("/"))
