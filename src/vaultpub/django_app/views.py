"""Django views for vaultpub."""
from __future__ import annotations

import re
from html import escape
from pathlib import PurePosixPath

from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from vaultpub.core.attachments import attachment_content_disposition, is_download_only_attachment
from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NavNode, NoteRecord, TextPageRecord, VaultIndex
from vaultpub.core.render import Renderer
from vaultpub.core.render.seo import build_meta_tags, build_page_description, build_page_title
from vaultpub.core.render.templates import (
    directory_page_html,
    directory_preview_map,
    directory_sibling_files_html,
    find_nav_directory,
    nav_tree_html,
    sidebar_graph_state,
    topbar_context_html_for_directory,
    topbar_context_html_for_note,
    topbar_context_html_for_text_page,
)
from vaultpub.core.security import is_path_excluded, is_path_public
from vaultpub.django_app.conf import get_default_config

_state_cache: dict = {}

_ABSOLUTE_ATTR_RE = re.compile(r'(?P<attr>\s(?:href|src)=["\'])(?P<url>/[^"\']*)(?P<quote>["\'])')


def _cache_key_for_config(config: PublisherConfig, cache_key: str | None = None) -> str:
    """
    Build a stable cache key for a rendered vault configuration.

    Explanation:
        Input: publisher config plus an optional caller-provided cache key.
        Output: string key for the in-process index/renderer cache.
        Where: Used by default and dynamic Django rendering helpers.
        What: Separates multiple vaults, URL prefixes, and scoped folder views.
    """
    if cache_key:
        return cache_key
    return "|".join(
        [
            str(config.vault_path),
            config.url_prefix,
            config.home_file or "",
            ",".join(config.include_folders),
            ",".join(config.force_include_regexes),
            ",".join(config.force_exclude_regexes),
        ]
    )


def build_state_for_config(
    config: PublisherConfig,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """
    Build or reuse the renderer state for a specific vault configuration.

    Explanation:
        Input: `PublisherConfig`, optional cache key, and refresh flag.
        Output: dict containing config, index, renderer, and indexer.
        Where: Used by reusable Django views and external multi-vault hosts.
        What: Allows callers to render several vaults dynamically without relying
        on a single `settings.VAULTPUB["default"]` entry.
    """
    global _state_cache
    config_key = _cache_key_for_config(config, cache_key)
    if force_refresh or config_key not in _state_cache:
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


def clear_state_cache(cache_key: str | None = None) -> None:
    """
    Clear cached Django renderer state.

    Explanation:
        Input: optional exact cache key.
        Output: None.
        Where: Used by management tools after vault configuration or files change.
        What: Drops one cached state or the entire cache so future requests rebuild
        the vault index from disk.
    """
    if cache_key is None:
        _state_cache.clear()
    else:
        _state_cache.pop(cache_key, None)


def _get_state():
    config = get_default_config()
    if config is None:
        raise RuntimeError("VAULTPUB not configured in Django settings")
    return build_state_for_config(config)


def _note_public_url(note: NoteRecord) -> str:
    return note.url_path


def _url_prefix(config: object) -> str:
    raw = str(getattr(config, "url_prefix", "/") or "/")
    if not raw.startswith("/"):
        raw = "/" + raw
    if not raw.endswith("/"):
        raw += "/"
    return raw


def _prefix_url(config: object, url: str | None) -> str | None:
    if url is None or not url.startswith("/") or url.startswith("//"):
        return url

    prefix = _url_prefix(config)
    if prefix == "/" or url.startswith(prefix):
        return url
    if url.startswith("/static/"):
        return url
    return prefix.rstrip("/") + url


def _prefix_html_urls(html: str, config: object) -> str:
    def _replace(match: re.Match[str]) -> str:
        url = match.group("url")
        prefixed = _prefix_url(config, url) or url
        return f'{match.group("attr")}{prefixed}{match.group("quote")}'

    return _ABSOLUTE_ATTR_RE.sub(_replace, html)


def _prefix_public_url(config: object, url: str) -> str:
    return _prefix_url(config, url) or url


def _build_url_maps(index: VaultIndex) -> tuple[dict[str, NoteRecord], dict[str, NoteRecord]]:
    canonical_to_note: dict[str, NoteRecord] = {}

    for note in index.notes_by_id.values():
        canonical = _note_public_url(note)
        canonical_to_note[canonical] = note
    return canonical_to_note, canonical_to_note


def _build_nav_html(index: VaultIndex, config: object) -> str:
    if index.nav_tree:
        return _prefix_html_urls("<ul>" + nav_tree_html(index.nav_tree) + "</ul>", config)
    return ""


def index(request: HttpRequest) -> HttpResponse:
    state = _get_state()
    home_note = state["indexer"].scanner.resolve_home(list(state["index"].notes_by_id.values()))
    if home_note is None:
        raise Http404("No notes found")
    return _render_note(request, home_note, state)


def page(request: HttpRequest, note_path: str) -> HttpResponse:
    state = _get_state()
    return _page_from_state(request, note_path, state)


def _page_from_state(request: HttpRequest, note_path: str, state: dict) -> HttpResponse:
    rel_path = "/" + note_path
    canonical_to_note, _all_urls_to_note = _build_url_maps(state["index"])
    if note_path.endswith("/"):
        directory = _resolve_directory(state["index"].nav_tree, note_path)
        if directory is not None and directory.path not in ("", "."):
            return _render_directory_page(request, directory, state)
        raise Http404("Not found")
    note = canonical_to_note.get(rel_path)
    if note:
        if not is_path_public(note.rel_path.as_posix(), state["config"]):
            raise Http404("Not found")
        return _render_note(request, note, state)

    # Check text pages
    tp = state["index"].text_pages_by_path.get(note_path)
    if tp is not None:
        if is_path_excluded(tp.rel_path.as_posix(), state["config"]):
            raise Http404("Not found")
        return _render_text_page(request, tp, state)

    raise Http404("Note not found")


def attachment(request: HttpRequest, asset_path: str) -> HttpResponse:
    state = _get_state()
    return _attachment_from_state(request, asset_path, state)


def _attachment_from_state(request: HttpRequest, asset_path: str, state: dict) -> HttpResponse:
    att = state["index"].attachments_by_path.get(asset_path)
    if att is None:
        raise Http404("Attachment not found")
    if is_path_excluded(asset_path, state["config"]):
        raise Http404("Attachment not found")
    fpath = state["config"].vault_path / asset_path
    if not fpath.exists():
        raise Http404("File not found")
    response = FileResponse(open(fpath, "rb"), content_type=att.mime_type)
    if is_download_only_attachment(att.rel_path):
        response["Content-Disposition"] = attachment_content_disposition(att.rel_path)
    return response


def api_page(request: HttpRequest, note_path: str) -> JsonResponse:
    state = _get_state()
    return _api_page_from_state(request, note_path, state)


def _api_page_from_state(request: HttpRequest, note_path: str, state: dict) -> JsonResponse:
    rel_path = "/" + note_path
    _canonical_to_note, all_urls_to_note = _build_url_maps(state["index"])
    note = all_urls_to_note.get(rel_path)
    if note:
        html = _prefix_html_urls(state["renderer"].render_note(note), state["config"])
        return JsonResponse({
            "id": note.id,
            "title": note.rel_path.name,
            "url": _prefix_url(state["config"], _note_public_url(note)),
            "html": html,
            "tags": list(note.tags),
            "headings": [{"level": h.level, "text": h.text, "slug": h.slug} for h in note.headings],
            "backlinks": list(note.backlinks),
        })

    # Check text pages
    tp = state["index"].text_pages_by_path.get(note_path)
    if tp is not None:
        code_html = _render_text_page_content(tp)
        return JsonResponse({
            "id": tp.id,
            "title": tp.title,
            "url": _prefix_url(state["config"], tp.url_path),
            "html": _prefix_html_urls(code_html, state["config"]),
            "tags": [],
            "headings": [],
            "backlinks": [],
        })

    return JsonResponse({"error": "Not found"}, status=404)


def api_search(request: HttpRequest) -> JsonResponse:
    state = _get_state()
    return _api_search_from_state(request, state)


def _api_search_from_state(request: HttpRequest, state: dict) -> JsonResponse:
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
            results.append({
                "title": doc["title"],
                "url": _prefix_url(state["config"], str(doc["url"])),
                "excerpt": doc["excerpt"],
                "tags": list(tags),
            })
            if len(results) >= 20:
                break
    return JsonResponse({"results": results})


def api_graph(request: HttpRequest) -> JsonResponse:
    state = _get_state()
    return _api_graph_from_state(request, state)


def _api_graph_from_state(request: HttpRequest, state: dict) -> JsonResponse:
    graph = state["index"].graph
    return JsonResponse({
        "nodes": [
            {"id": n.id, "label": n.label, "group": n.group, "url": _prefix_url(state["config"], n.url)}
            for n in graph.nodes
        ],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in graph.edges],
    })


def api_local_graph(request: HttpRequest, note_path: str) -> JsonResponse:
    state = _get_state()
    return _api_local_graph_from_state(request, note_path, state)


def _api_local_graph_from_state(request: HttpRequest, note_path: str, state: dict) -> JsonResponse:
    graph = state["index"].graph
    note_id = None
    _canonical_to_note, all_urls_to_note = _build_url_maps(state["index"])
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
        "nodes": [
            {"id": n.id, "label": n.label, "group": n.group, "url": _prefix_url(state["config"], n.url)}
            for n in local_nodes
        ],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in local_edges],
    })


def render_index_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> HttpResponse:
    """
    Render a vault home page from a caller-provided config.

    Explanation:
        Input: Django request, dynamic `PublisherConfig`, optional cache key, and refresh flag.
        Output: rendered vault home response.
        Where: Used by host Django projects that manage multiple vaults.
        What: Builds the vault index dynamically and resolves the configured or
        first visible home note inside the current scope.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    home_note = state["indexer"].scanner.resolve_home(list(state["index"].notes_by_id.values()))
    if home_note is None:
        raise Http404("No notes found")
    return _render_note(request, home_note, state)


def render_page_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    note_path: str,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> HttpResponse:
    """
    Render a note, text page, or directory from a caller-provided config.

    Explanation:
        Input: request, dynamic config, URL path inside the vault, and cache controls.
        Output: rendered HTML response or 404.
        Where: Used by multi-vault Django integrations.
        What: Reuses the normal Django rendering pipeline without depending on
        `settings.VAULTPUB`.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _page_from_state(request, note_path, state)


def render_attachment_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    asset_path: str,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> HttpResponse:
    """
    Serve a vault attachment from a caller-provided config.

    Explanation:
        Input: request, dynamic config, asset path, and cache controls.
        Output: streaming file response.
        Where: Used by multi-vault Django integrations.
        What: Resolves attachments from the scoped dynamic index and streams the
        file instead of loading it fully into memory.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _attachment_from_state(request, asset_path, state)


def render_api_page_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    note_path: str,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> JsonResponse:
    """
    Render the hover-preview page API from a caller-provided config.

    Explanation:
        Input: request, dynamic config, URL path inside the vault, and cache controls.
        Output: JSON page payload.
        Where: Used by multi-vault Django integrations.
        What: Keeps hover previews scoped to the same dynamic vault index as pages.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _api_page_from_state(request, note_path, state)


def render_api_search_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> JsonResponse:
    """
    Render the search API from a caller-provided config.

    Explanation:
        Input: request, dynamic config, and cache controls.
        Output: JSON search results.
        Where: Used by multi-vault Django integrations.
        What: Searches only the notes/text pages present in the scoped dynamic index.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _api_search_from_state(request, state)


def render_api_graph_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> JsonResponse:
    """
    Render the graph API from a caller-provided config.

    Explanation:
        Input: request, dynamic config, and cache controls.
        Output: JSON graph data.
        Where: Used by multi-vault Django integrations.
        What: Emits graph nodes and edges from the scoped dynamic index.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _api_graph_from_state(request, state)


def render_api_local_graph_with_config(
    request: HttpRequest,
    config: PublisherConfig,
    note_path: str,
    cache_key: str | None = None,
    force_refresh: bool = False,
) -> JsonResponse:
    """
    Render the local graph API from a caller-provided config.

    Explanation:
        Input: request, dynamic config, note path, and cache controls.
        Output: JSON graph data around one note.
        Where: Used by multi-vault Django integrations.
        What: Keeps local graph responses aligned with the scoped dynamic index.
    """
    state = build_state_for_config(config, cache_key=cache_key, force_refresh=force_refresh)
    return _api_local_graph_from_state(request, note_path, state)


def _render_note(request: HttpRequest, note: NoteRecord, state: dict | None = None) -> HttpResponse:
    state = state or _get_state()
    config = state["config"]
    index: VaultIndex = state["index"]
    renderer: Renderer = state["renderer"]
    current_path = _prefix_url(config, _note_public_url(note)) or _note_public_url(note)

    context = {
        "page_body_html": _prefix_html_urls(renderer.render_article_html(note, current_path), config),
        "title": build_page_title(note, config),
        "site_name": config.site_name,
        "description": build_page_description(note, config),
        "note_id": note.id,
        "url_path": _prefix_url(config, _note_public_url(note)),
        "nav_html": _build_nav_html(index, config),
        "toc_html": _prefix_html_urls(renderer.render_toc_html(note), config),
        "backlinks_html": _prefix_html_urls(renderer.render_backlinks_html(note), config),
        "realtime": config.realtime,
        "site_logo": config.site_logo,
        "show_theme_toggle": config.show_theme_toggle,
        "show_search": config.show_search,
        "url_prefix": _url_prefix(config),
        "seo_head": build_meta_tags(note, config),
        "topbar_context_html": topbar_context_html_for_note(
            note,
            url_transform=lambda url: _prefix_public_url(config, url),
        ),
    }
    show_graph, graph_note_id = sidebar_graph_state(config, index.graph, note)
    context["show_graph"] = show_graph
    context["graph_note_id"] = graph_note_id
    return render(request, "vaultpub/page.html", context)


def _render_text_page(request: HttpRequest, tp: TextPageRecord, state: dict | None = None) -> HttpResponse:
    state = state or _get_state()
    config = state["config"]
    index = state["index"]
    current_path = _prefix_url(config, tp.url_path) or tp.url_path

    context = {
        "page_body_html": _prefix_html_urls(_render_text_page_content(tp, current_path), config),
        "title": tp.title,
        "site_name": config.site_name,
        "description": tp.excerpt,
        "note_id": tp.id,
        "url_path": _prefix_url(config, tp.url_path),
        "nav_html": _build_nav_html(index, config),
        "toc_html": "",
        "backlinks_html": "",
        "realtime": config.realtime,
        "site_logo": config.site_logo,
        "show_theme_toggle": config.show_theme_toggle,
        "show_search": config.show_search,
        "url_prefix": _url_prefix(config),
        "seo_head": f"<title>{escape(tp.title)} - {escape(config.site_name)}</title>",
        "topbar_context_html": topbar_context_html_for_text_page(
            tp,
            url_transform=lambda url: _prefix_public_url(config, url),
        ),
    }
    show_graph, graph_note_id = sidebar_graph_state(config, index.graph, None)
    context["show_graph"] = show_graph
    context["graph_note_id"] = graph_note_id
    return render(request, "vaultpub/page.html", context)


def _render_directory_page(request: HttpRequest, directory: NavNode, state: dict | None = None) -> HttpResponse:
    state = state or _get_state()
    config = state["config"]
    index: VaultIndex = state["index"]

    page_body_html = directory_page_html(
        directory,
        current_path=_prefix_url(config, directory.url) or directory.url,
        content_previews=directory_preview_map(
            index.notes_by_id.values(),
            index.text_pages_by_path.values(),
        ),
    )
    sidebar_right_html = _prefix_html_urls(directory_sibling_files_html(index.nav_tree, directory), config)
    context = {
        "page_body_html": _prefix_html_urls(page_body_html, config),
        "title": f"{directory.label}/ - {config.site_name}",
        "site_name": config.site_name,
        "description": f"{directory.label}/",
        "note_id": directory.path,
        "url_path": _prefix_url(config, directory.url),
        "nav_html": _build_nav_html(index, config),
        "toc_html": "",
        "backlinks_html": "",
        "sidebar_right_html": sidebar_right_html,
        "sidebar_right_title": "Directory",
        "realtime": config.realtime,
        "site_logo": config.site_logo,
        "show_theme_toggle": config.show_theme_toggle,
        "show_search": config.show_search,
        "url_prefix": _url_prefix(config),
        "seo_head": f"<title>{escape(directory.label)}/ - {escape(config.site_name)}</title>",
        "topbar_context_html": topbar_context_html_for_directory(
            PurePosixPath(directory.path),
            current_url=directory.url,
            url_transform=lambda url: _prefix_public_url(config, url),
        ),
    }
    show_graph, graph_note_id = sidebar_graph_state(config, index.graph, None)
    context["show_graph"] = show_graph
    context["graph_note_id"] = graph_note_id
    return render(request, "vaultpub/page.html", context)


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
