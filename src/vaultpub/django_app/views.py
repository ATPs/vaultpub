"""Django views for vaultpub."""
from __future__ import annotations

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NoteRecord, VaultIndex
from vaultpub.core.render import Renderer
from vaultpub.core.render.seo import build_meta_tags, build_page_description, build_page_title
from vaultpub.core.render.templates import nav_tree_html
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


def _note_public_url(note: NoteRecord) -> str:
    permalink = note.frontmatter.get("permalink")
    if permalink:
        return "/" + str(permalink).lstrip("/")
    return note.url_path


def _build_url_maps(index: VaultIndex) -> tuple[dict[str, NoteRecord], dict[str, str], dict[str, NoteRecord]]:
    canonical_to_note: dict[str, NoteRecord] = {}
    redirect_map: dict[str, str] = {}
    all_urls_to_note: dict[str, NoteRecord] = {}

    for note in index.notes_by_id.values():
        canonical = _note_public_url(note)
        canonical_to_note[canonical] = note
        all_urls_to_note[canonical] = note
        all_urls_to_note[note.url_path] = note
        if note.url_path != canonical:
            redirect_map[note.url_path] = canonical

        for alias in note.aliases:
            alias_path = "/" + alias.lstrip("/")
            all_urls_to_note[alias_path] = note
            if alias_path != canonical:
                redirect_map[alias_path] = canonical

    return canonical_to_note, redirect_map, all_urls_to_note


def _build_nav_html(index: VaultIndex) -> str:
    if index.nav_tree:
        return "<ul>" + nav_tree_html(index.nav_tree) + "</ul>"
    return ""


def index(request: HttpRequest) -> HttpResponse:
    state = _get_state()
    home_note = state["indexer"].scanner.resolve_home(list(state["index"].notes_by_id.values()))
    if home_note is None:
        raise Http404("No notes found")
    return _render_note(request, home_note)


def page(request: HttpRequest, note_path: str) -> HttpResponse:
    state = _get_state()
    rel_path = "/" + note_path
    canonical_to_note, redirect_map, _all_urls_to_note = _build_url_maps(state["index"])
    note = canonical_to_note.get(rel_path)
    if note:
        if not is_path_public(note.rel_path.as_posix(), state["config"]):
            raise Http404("Not found")
        return _render_note(request, note)
    if rel_path in redirect_map:
        response = HttpResponse(status=301)
        response["Location"] = redirect_map[rel_path]
        return response
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
    _canonical_to_note, _redirect_map, all_urls_to_note = _build_url_maps(state["index"])
    note = all_urls_to_note.get(rel_path)
    if note:
        html = state["renderer"].render_note(note)
        return JsonResponse({
            "id": note.id,
            "title": note.title,
            "url": _note_public_url(note),
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
    _canonical_to_note, _redirect_map, all_urls_to_note = _build_url_maps(state["index"])
    note = all_urls_to_note.get("/" + note_path)
    if note:
        note_id = note.id
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


def _render_note(request: HttpRequest, note: NoteRecord) -> HttpResponse:
    state = _get_state()
    config = state["config"]
    index: VaultIndex = state["index"]
    renderer: Renderer = state["renderer"]

    context = {
        "content": renderer.render_note(note),
        "title": build_page_title(note, config),
        "site_name": config.site_name,
        "description": build_page_description(note, config),
        "note_id": note.id,
        "url_path": _note_public_url(note),
        "nav_html": _build_nav_html(index),
        "toc_html": renderer.render_toc_html(note),
        "backlinks_html": renderer.render_backlinks_html(note),
        "realtime": config.realtime,
        "site_logo": config.site_logo,
        "show_theme_toggle": config.show_theme_toggle,
        "show_graph": config.show_graph or config.show_local_graph,
        "show_search": config.show_search,
        "seo_head": build_meta_tags(note, config),
    }
    return render(request, "vaultpub/page.html", context)
