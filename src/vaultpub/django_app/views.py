"""Django views for vaultpub."""
from __future__ import annotations

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse

from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.render import Renderer
from vaultpub.core.render.seo import build_meta_tags
from vaultpub.core.render.templates import base_page_template, nav_tree_html
from vaultpub.core.security import is_path_public
from vaultpub.django_app.conf import get_default_config

_state_cache: dict = {}


def _get_state():
    global _state_cache
    config = get_default_config()
    if config is None:
        raise RuntimeError("VAULTPUB not configured in Django settings")
    config_key = str(config.vault_path)
    if config_key not in _state_cache:
        indexer = VaultIndexer(config)
        vault_index = indexer.build()
        renderer = Renderer(config, vault_index)
        _state_cache[config_key] = {
            "config": config,
            "index": vault_index,
            "renderer": renderer,
            "indexer": indexer,
        }
    return _state_cache[config_key]


def index(request: HttpRequest) -> HttpResponse:
    state = _get_state()
    home_note = state["indexer"].scanner.resolve_home(list(state["index"].notes_by_id.values()))
    if home_note is None:
        raise Http404("No notes found")
    return _render_note(request, home_note)


def page(request: HttpRequest, note_path: str) -> HttpResponse:
    state = _get_state()
    rel_path = "/" + note_path
    for note in state["index"].notes_by_id.values():
        if note.url_path == rel_path:
            if not is_path_public(note.rel_path.as_posix(), state["config"]):
                raise Http404("Not found")
            return _render_note(request, note)
    raise Http404("Note not found")


def attachment(request: HttpRequest, asset_path: str) -> HttpResponse:
    state = _get_state()
    att = state["index"].attachments_by_path.get(asset_path)
    if att is None:
        raise Http404("Attachment not found")
    fpath = state["config"].vault_path / asset_path
    if not fpath.exists():
        raise Http404("File not found")
    content = fpath.read_bytes()
    return HttpResponse(content, content_type=att.mime_type)


def api_page(request: HttpRequest, note_path: str) -> JsonResponse:
    state = _get_state()
    rel_path = "/" + note_path
    for note in state["index"].notes_by_id.values():
        if note.url_path == rel_path:
            html = state["renderer"].render_note(note)
            return JsonResponse({
                "id": note.id,
                "title": note.title,
                "url": note.url_path,
                "html": html,
                "tags": list(note.tags),
                "headings": [{"level": h.level, "text": h.text, "slug": h.slug} for h in note.headings],
                "backlinks": list(note.backlinks),
            })
    return JsonResponse({"error": "Not found"}, status=404)


def api_search(request: HttpRequest) -> JsonResponse:
    state = _get_state()
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})
    q_lower = q.lower()
    results = []
    for doc in state["index"].search_documents:
        title = str(doc.get("title", ""))
        content = str(doc.get("content", ""))
        tags = doc.get("tags", [])
        if q_lower in title.lower() or q_lower in content.lower() or any(q_lower in str(t).lower() for t in tags):
            results.append({"title": doc["title"], "url": doc["url"], "excerpt": doc["excerpt"], "tags": list(tags)})
            if len(results) >= 20:
                break
    return JsonResponse({"results": results})


def api_graph(request: HttpRequest) -> JsonResponse:
    state = _get_state()
    graph = state["index"].graph
    return JsonResponse({
        "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in graph.nodes],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in graph.edges],
    })


def api_local_graph(request: HttpRequest, note_path: str) -> JsonResponse:
    state = _get_state()
    graph = state["index"].graph
    note_id = None
    for note in state["index"].notes_by_id.values():
        if note.url_path == "/" + note_path:
            note_id = note.id
            break
    if not note_id:
        return JsonResponse({"nodes": [], "edges": []})
    nid = f"note:{note_id}"
    local_edges = [e for e in graph.edges if e.source == nid or e.target == nid]
    local_ids = {e.source for e in local_edges} | {e.target for e in local_edges}
    local_nodes = [n for n in graph.nodes if n.id in local_ids]
    return JsonResponse({
        "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in local_nodes],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in local_edges],
    })


def _render_note(request: HttpRequest, note: object) -> HttpResponse:
    state = _get_state()
    body_html = state["renderer"].render_page_html(note)
    nav_html = ""
    if state["index"].nav_tree:
        nav_html = "<ul>" + nav_tree_html(state["index"].nav_tree) + "</ul>"
    head = build_meta_tags(note, state["config"])
    page = base_page_template(body_html, nav_html, head, state["config"])
    return HttpResponse(page)
