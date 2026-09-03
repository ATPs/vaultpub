"""Web routes for the standalone ASGI app."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from html import escape
from pathlib import PurePosixPath
from urllib.parse import urlparse

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from vaultpub.core.attachments import (
    attachment_content_disposition,
    attachment_mime_type,
    is_download_only_attachment,
)
from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import AttachmentRecord, NavNode, NoteRecord, TextPageRecord, VaultIndex
from vaultpub.core.navigation_order import (
    NavigationOrderConflict,
    NavigationOrderError,
    order_editor_payload,
    reset_navigation_order,
    save_navigation_order,
)
from vaultpub.core.paths import (
    API_URL_PREFIX,
    SETTINGS_URL_PREFIX,
    SLIDES_FOLDER_URL_PREFIX,
    SLIDES_URL_PREFIX,
    SLIDES_VAULT_URL,
    safe_join,
)
from vaultpub.core.render.renderer import Renderer
from vaultpub.core.render.seo import build_meta_tags
from vaultpub.core.render.slides import (
    SlideOptions,
    collect_directory_notes,
    collect_slide_scope_directories,
    describe_slide_note,
    slide_options,
    slide_split_override,
    validated_slide_deck_order,
)
from vaultpub.core.render.templates import (
    base_page_template,
    defer_slide_media_html,
    directory_page_html,
    directory_preview_map,
    directory_sibling_files_html,
    find_nav_directory,
    graph_container_html,
    multi_note_slide_placeholders_html,
    multi_note_slide_sections_html,
    nav_tree_html,
    order_editor_page_html,
    sidebar_graph_state,
    slide_sections_html,
    slides_page_template,
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
    shutdown_signal: threading.Event | None = None


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


async def order_editor(request: Request) -> HTMLResponse:
    state = _get_state(request)
    try:
        payload = order_editor_payload(state.config, state.index, request.query_params.get("directory"))
    except NavigationOrderError:
        return HTMLResponse("Not found", status_code=404)
    nav_html = ""
    if state.index.nav_tree:
        nav_html = "<ul>" + nav_tree_html(state.index.nav_tree) + "</ul>"
    page_str = base_page_template(
        order_editor_page_html(
            f"{API_URL_PREFIX}/settings/order", f"{API_URL_PREFIX}/settings/order", payload["directory"]
        ),
        nav_html,
        f"<title>Custom order - {escape(state.config.site_name)}</title>",
        state.config,
        sidebar_right_title="Order",
        order_editor_url=f"{SETTINGS_URL_PREFIX}/order",
    )
    return HTMLResponse(page_str)


async def api_order_editor(request: Request) -> JSONResponse:
    state = _get_state(request)
    directory = request.query_params.get("directory")
    if request.method == "GET":
        try:
            return JSONResponse(order_editor_payload(state.config, state.index, directory))
        except NavigationOrderError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)

    if not _is_same_origin(request):
        return JSONResponse({"error": "Cross-origin ordering requests are not allowed"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Expected a JSON request body"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Expected a JSON object"}, status_code=400)

    directory = body.get("directory")
    try:
        if body.get("action") == "reset":
            reset_navigation_order(state.config, state.index, directory, body.get("revision"))
        elif body.get("action") == "save":
            save_navigation_order(
                state.config,
                state.index,
                directory,
                body.get("folders"),
                body.get("files"),
                body.get("revision"),
            )
        else:
            return JSONResponse({"error": "Unknown ordering action"}, status_code=400)
    except NavigationOrderConflict as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)
    except NavigationOrderError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    _refresh_state(state)
    return JSONResponse(order_editor_payload(state.config, state.index, directory))


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


async def slides(request: Request) -> HTMLResponse:
    state = _get_state(request)
    path = request.path_params.get("path", "")
    note = _build_url_maps(state.index)[0].get("/" + path)
    if note is None or not is_path_public(note.rel_path.as_posix(), state.config):
        return HTMLResponse("Not found", status_code=404)

    options = slide_options(note.frontmatter)
    split_override = slide_split_override(
        request.query_params.get("split"), request.cookies.get("vaultpub_slide_split")
    )
    page_html = slides_page_template(
        title=f"{note.title} - Presentation",
        slides_html=slide_sections_html(state.renderer.render_slides(note, split_override=split_override)),
        options=options,
        return_url=note.url_path,
        return_label="Article",
        split_override=split_override,
    )
    return HTMLResponse(page_html, headers={"Vary": "Cookie"})


async def slides_folder(request: Request) -> HTMLResponse:
    state = _get_state(request)
    path = request.path_params.get("path", "")
    directory = _resolve_directory(state.index.nav_tree, path)
    if directory is None or directory.path in ("", "."):
        return HTMLResponse("Not found", status_code=404)

    order = validated_slide_deck_order(request.query_params.get("sort")) or "predefined"
    notes = collect_directory_notes(directory, state.index, order)
    if not notes:
        return HTMLResponse("Not found", status_code=404)

    split_override = slide_split_override(
        request.query_params.get("split"), request.cookies.get("vaultpub_slide_split")
    )
    page_html = slides_page_template(
        title=f"{directory.label} - Presentation",
        slides_html=multi_note_slide_placeholders_html(notes),
        options=SlideOptions(),
        return_url=directory.url,
        return_label="Folder",
        split_override=split_override,
        slide_manifest=_multi_note_slide_manifest(notes, split_override),
    )
    return HTMLResponse(page_html, headers={"Vary": "Cookie"})


async def slides_vault(request: Request) -> HTMLResponse:
    state = _get_state(request)
    if state.index.nav_tree is None:
        return HTMLResponse("Not found", status_code=404)

    order = validated_slide_deck_order(request.query_params.get("sort")) or "predefined"
    notes = collect_directory_notes(state.index.nav_tree, state.index, order)
    if not notes:
        return HTMLResponse("Not found", status_code=404)

    split_override = slide_split_override(
        request.query_params.get("split"), request.cookies.get("vaultpub_slide_split")
    )
    return HTMLResponse(slides_page_template(
        title=f"{state.config.site_name} - Presentation",
        slides_html=multi_note_slide_placeholders_html(notes),
        options=SlideOptions(),
        return_url="/",
        return_label="Vault",
        split_override=split_override,
        slide_manifest=_multi_note_slide_manifest(notes, split_override),
    ), headers={"Vary": "Cookie"})


async def api_slides(request: Request) -> JSONResponse:
    """Return one lazily rendered slide note for a multi-note deck."""
    state = _get_state(request)
    path = request.path_params.get("path", "")
    note = _build_url_maps(state.index)[0].get("/" + path)
    if note is None or not is_path_public(note.rel_path.as_posix(), state.config):
        return JSONResponse({"error": "Not found"}, status_code=404)

    split_override = slide_split_override(
        request.query_params.get("split"), request.cookies.get("vaultpub_slide_split")
    )
    descriptor = describe_slide_note(note, split_override)
    rendered = state.renderer.render_slides(
        note,
        heading_namespace=f"slide-{note.id[:12]}",
        split_override=split_override,
    )
    return JSONResponse(
        {
            "noteId": note.id,
            "sourcePath": note.rel_path.as_posix(),
            "slides": [
                {
                    "index": slide.index,
                    "title": descriptor.fragments[slide.index].title,
                    "html": defer_slide_media_html(slide.html),
                }
                for slide in rendered
            ],
        },
        headers={"Cache-Control": "no-store", "Vary": "Cookie"},
    )


async def attachment(request: Request) -> Response:
    state = _get_state(request)
    path = request.path_params.get("path", "")

    asset = _resolve_public_asset(state.renderer, state.index, path)
    if asset is None:
        return HTMLResponse("Not found", status_code=404)

    if is_path_excluded(path, state.config):
        return HTMLResponse("Not found", status_code=404)

    fpath = safe_join(state.config.vault_path, path)
    if not fpath.exists():
        return HTMLResponse("Not found", status_code=404)

    content = fpath.read_bytes()
    headers: dict[str, str] = {}
    media_type = attachment_mime_type(asset.rel_path)
    if isinstance(asset, AttachmentRecord) and is_download_only_attachment(asset.rel_path):
        headers["Content-Disposition"] = attachment_content_disposition(asset.rel_path)
    return Response(content, media_type=media_type, headers=headers)


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


def _slide_launch_data(state: AppState) -> tuple[str | None, list[dict[str, str]]]:
    nav_tree = state.index.nav_tree
    if nav_tree is None or not collect_directory_notes(nav_tree, state.index):
        return None, []

    scopes = [{"label": "Whole vault", "url": SLIDES_VAULT_URL}]
    scopes.extend(
        {"label": f"{directory.path}/", "url": f"{SLIDES_FOLDER_URL_PREFIX}/{directory.path}/"}
        for directory in collect_slide_scope_directories(nav_tree, state.index)
    )
    return scopes[0]["url"], scopes


def _refresh_state(state: AppState) -> None:
    index = state.indexer.build()
    renderer = Renderer(state.config, index)
    state.index = index
    state.renderer = renderer
    if state.rt_state is not None:
        state.rt_state.index = index
        state.rt_state.renderer = renderer


def _is_same_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.netloc == request.headers.get("host")


def _multi_note_slides_html(notes: list[NoteRecord], renderer: Renderer, split_override: str | None) -> str:
    return multi_note_slide_sections_html(
        (
            note,
            renderer.render_slides(
                note,
                heading_namespace=f"slide-{note.id[:12]}",
                split_override=split_override,
            ),
        )
        for note in notes
    )


def _multi_note_slide_manifest(notes: list[NoteRecord], split_override: str | None) -> list[dict[str, object]]:
    return [
        {
            "id": descriptor.id,
            "title": descriptor.title,
            "sourcePath": descriptor.source_path,
            "payloadUrl": f"{API_URL_PREFIX}/slides{note.url_path}",
            "fragments": [{"index": fragment.index, "title": fragment.title} for fragment in descriptor.fragments],
        }
        for note in notes
        for descriptor in [describe_slide_note(note, split_override)]
    ]


def _render_note_page(request: Request, note: NoteRecord) -> HTMLResponse:
    state = _get_state(request)
    vault_slides_url, slide_scopes = _slide_launch_data(state)
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
    topbar_context_html = topbar_context_html_for_note(note, present_url=f"{SLIDES_URL_PREFIX}{note.url_path}")
    page_str = base_page_template(
        body_html,
        nav_html,
        head,
        state.config,
        sidebar_right_html,
        graph_html=graph_html,
        topbar_context_html=topbar_context_html,
        vault_slides_url=vault_slides_url,
        slide_scopes=slide_scopes,
        order_editor_url=f"{SETTINGS_URL_PREFIX}/order",
    )
    return HTMLResponse(page_str)


def _render_directory_page(request: Request, directory: NavNode) -> HTMLResponse:
    state = _get_state(request)
    vault_slides_url, slide_scopes = _slide_launch_data(state)
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
        vault_slides_url=vault_slides_url,
        slide_scopes=slide_scopes,
        order_editor_url=f"{SETTINGS_URL_PREFIX}/order",
    )
    return HTMLResponse(page_str)


def _render_text_page(request: Request, tp: TextPageRecord) -> HTMLResponse:
    state = _get_state(request)
    vault_slides_url, slide_scopes = _slide_launch_data(state)
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
        vault_slides_url=vault_slides_url,
        slide_scopes=slide_scopes,
        order_editor_url=f"{SETTINGS_URL_PREFIX}/order",
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


def _resolve_public_asset(renderer: Renderer, index: VaultIndex, path: str) -> AttachmentRecord | TextPageRecord | None:
    att = index.attachments_by_path.get(path)
    if att is not None:
        return att
    dyn_att = renderer.dynamic_attachments_by_path.get(path)
    if dyn_att is not None:
        return dyn_att
    return renderer.dynamic_text_pages_by_path.get(path)
