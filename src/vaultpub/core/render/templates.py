"""HTML templates for page layout."""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from html import escape
from pathlib import PurePosixPath

from vaultpub.core.models import GraphData, Heading, NavNode, NoteRecord, TextPageRecord
from vaultpub.core.paths import directory_display_name, directory_path_to_url_path
from vaultpub.core.render.slides import RenderedSlide, SlideOptions


def build_local_graph(graph: GraphData, note: NoteRecord) -> GraphData:
    """Return the subgraph directly connected to a note."""
    note_node_id = f"note:{note.id}"
    local_edges = [edge for edge in graph.edges if edge.source == note_node_id or edge.target == note_node_id]
    local_ids = {edge.source for edge in local_edges} | {edge.target for edge in local_edges}
    local_nodes = [node for node in graph.nodes if node.id in local_ids]
    return GraphData(nodes=local_nodes, edges=local_edges)


def sidebar_graph_state(
    config: object | None,
    graph: GraphData | None = None,
    note: NoteRecord | None = None,
) -> tuple[bool, str | None]:
    """Return whether a sidebar graph should render, and its local note id if applicable."""
    if config is None or graph is None:
        return False, None

    show_local_graph = getattr(config, "show_local_graph", True)
    show_graph = getattr(config, "show_graph", True)

    if note is not None and show_local_graph:
        local_graph = build_local_graph(graph, note)
        if len(local_graph.nodes) >= 3:
            return True, f"note:{note.id}"
        return False, None

    if show_graph and len(graph.nodes) >= 3:
        return True, None

    return False, None


def graph_container_html(show_graph: bool, graph_note_id: str | None = None) -> str:
    """Render the sidebar graph container when the page graph is meaningful."""
    if not show_graph:
        return ""

    note_attr = f' data-graph-note-id="{escape(graph_note_id)}"' if graph_note_id else ""
    return f'<div id="graph-container" class="graph-container"{note_attr}></div>'


def _preview_text(content: str) -> str:
    lines: list[str] = []
    for raw_line in content.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        lines.append(line)
        if len(lines) == 2:
            break
    return "\n".join(lines)


def directory_preview_map(
    notes: Iterable[NoteRecord],
    text_pages: Iterable[TextPageRecord],
) -> dict[str, str]:
    previews: dict[str, str] = {}

    for note in notes:
        preview = _preview_text(note.plain_text)
        if preview:
            previews[note.rel_path.as_posix()] = preview

    for text_page in text_pages:
        preview = _preview_text(text_page.plain_text)
        if preview:
            previews[text_page.rel_path.as_posix()] = preview

    return previews


def _breadcrumbs_html(
    rel_path: PurePosixPath,
    current_url: str,
    url_transform: Callable[[str], str] | None = None,
) -> str:
    home_url = _transform_url("/", url_transform)
    segments = [f'<a href="{escape(home_url, quote=True)}" class="topbar-breadcrumb-link">Home</a>']
    parts = list(rel_path.parts)
    dir_parts: list[str] = []

    for part in parts[:-1]:
        dir_parts.append(part)
        dir_url = _transform_url(directory_path_to_url_path("/".join(dir_parts)), url_transform)
        segments.append('<span class="topbar-breadcrumb-sep">/</span>')
        segments.append(
            f'<a href="{escape(dir_url, quote=True)}" class="topbar-breadcrumb-link topbar-breadcrumb-segment">'
            f"{escape(part)}</a>"
        )

    if parts:
        final_url = _transform_url(current_url, url_transform)
        segments.append('<span class="topbar-breadcrumb-sep">/</span>')
        segments.append(
            f'<a href="{escape(final_url, quote=True)}" class="topbar-breadcrumb-link topbar-breadcrumb-current">'
            f"{escape(parts[-1])}</a>"
        )

    return "".join(segments)


def _preferred_heading(note: NoteRecord) -> Heading | None:
    if not note.headings:
        return None
    for heading in note.headings:
        if heading.level > 1:
            return heading
    return note.headings[0]


def _format_size(size: int) -> str:
    value = float(size)
    units = ("B", "KB", "MB", "GB")
    unit = units[0]
    for candidate in units:
        unit = candidate
        if value < 1024 or candidate == units[-1]:
            break
        value /= 1024

    if unit == "B":
        return f"{int(value)} {unit}"
    if value >= 10:
        return f"{value:.0f} {unit}"
    return f"{value:.1f} {unit}"


def _language_label(text_page: TextPageRecord) -> str:
    if text_page.language:
        normalized = text_page.language.replace("-", " ").replace("_", " ")
        return " ".join(part.capitalize() for part in normalized.split())

    suffix = text_page.rel_path.suffix.lstrip(".")
    return suffix.upper() if suffix else "Text"


def topbar_context_html_for_note(
    note: NoteRecord,
    url_transform: Callable[[str], str] | None = None,
    present_url: str | None = None,
) -> str:
    heading = _preferred_heading(note)
    heading_href = f' href="#{escape(heading.slug, quote=True)}"' if heading is not None else ""
    heading_hidden = "" if heading is not None else " hidden"
    heading_text = escape(heading.text) if heading is not None else ""

    present_attr = f' data-slide-note-url="{escape(present_url, quote=True)}"' if present_url else ""
    return f"""\
<div class="topbar-context topbar-context-note" data-topbar-context="note"{present_attr}>
  <nav class="topbar-breadcrumbs" aria-label="Current location">
    {_breadcrumbs_html(note.rel_path, note.url_path, url_transform)}
  </nav>
  <a class="topbar-current-heading" data-current-heading aria-live="polite"{heading_href}{heading_hidden}>{heading_text}</a>
</div>"""


def topbar_context_html_for_text_page(
    text_page: TextPageRecord,
    url_transform: Callable[[str], str] | None = None,
) -> str:
    return f"""\
<div class="topbar-context topbar-context-code" data-topbar-context="code">
  <nav class="topbar-breadcrumbs" aria-label="Current location">
    {_breadcrumbs_html(text_page.rel_path, text_page.url_path, url_transform)}
  </nav>
  <div class="topbar-code-tools">
    <span class="topbar-code-meta">{escape(_language_label(text_page))} &middot; {_format_size(text_page.size)}</span>
    <button class="topbar-code-btn" type="button" data-code-action="copy-path"
            data-code-path="{escape(text_page.rel_path.as_posix(), quote=True)}">Copy path</button>
    <button class="topbar-code-btn" type="button" data-code-action="toggle-wrap" aria-pressed="false">Wrap</button>
  </div>
</div>"""


def topbar_context_html_for_directory(
    dir_path: PurePosixPath,
    current_url: str,
    url_transform: Callable[[str], str] | None = None,
) -> str:
    directory_name = escape(directory_display_name(dir_path))
    return f"""\
<div class="topbar-context topbar-context-note" data-topbar-context="directory">
  <nav class="topbar-breadcrumbs" aria-label="Current location">
    {_breadcrumbs_html(dir_path, current_url, url_transform)}
  </nav>
  <span class="topbar-current-heading" data-current-heading>{directory_name}/</span>
</div>"""


def slide_sections_html(slides: Iterable[RenderedSlide]) -> str:
    """Render sanitized slide fragments as Reveal sections."""
    return "".join(
        f'<section class="vaultpub-slide" data-source-note="{escape(slide.source_note_id, quote=True)}" '
        f'data-source-path="{escape(slide.source_path, quote=True)}">'
        f'<div class="markdown-body vaultpub-slide-content">{slide.html}</div></section>'
        for slide in slides
    )


def multi_note_slide_sections_html(note_slides: Iterable[tuple[NoteRecord, Iterable[RenderedSlide]]]) -> str:
    """Render multi-note decks with a source-note divider before every note."""
    sections: list[str] = []
    for note, slides in note_slides:
        note_id = escape(note.id, quote=True)
        source_path = escape(note.rel_path.as_posix(), quote=True)
        sections.append(
            f'<section class="vaultpub-slide vaultpub-slide-divider" data-source-note="{note_id}" '
            f'data-source-path="{source_path}" data-slide-kind="note-divider">'
            '<div class="markdown-body vaultpub-slide-content">'
            '<p class="vaultpub-slide-divider-kicker">Now showing</p>'
            f'<h1>{escape(note.title)}</h1>'
            f'<p class="vaultpub-slide-divider-path">{escape(note.rel_path.as_posix())}</p>'
            '</div></section>'
        )
        sections.append(slide_sections_html(slides))
    return "".join(sections)


def multi_note_slide_placeholders_html(notes: Iterable[NoteRecord]) -> str:
    """Render lightweight stable Reveal slots for a lazily loaded note deck."""
    sections: list[str] = []
    for note_index, note in enumerate(notes):
        note_id = escape(note.id, quote=True)
        source_path = escape(note.rel_path.as_posix(), quote=True)
        sections.append(
            f'<section class="vaultpub-note-slot" data-vaultpub-note-index="{note_index}" '
            f'data-source-note="{note_id}" data-source-path="{source_path}">'
            f'<section class="vaultpub-slide vaultpub-slide-divider" data-source-note="{note_id}" '
            f'data-source-path="{source_path}" data-slide-kind="note-divider">'
            '<div class="markdown-body vaultpub-slide-content">'
            '<p class="vaultpub-slide-divider-kicker">Now showing</p>'
            f'<h1>{escape(note.title)}</h1>'
            f'<p class="vaultpub-slide-divider-path">{source_path}</p>'
            '</div></section></section>'
        )
    return "".join(sections)


_SLIDE_MEDIA_SRC_RE = re.compile(r"(<(?:img|audio|video|iframe)\b[^>]*?)\ssrc=", re.IGNORECASE)
_SLIDE_AV_TAG_RE = re.compile(r"<(audio|video)\b(?![^>]*\bpreload=)", re.IGNORECASE)


def defer_slide_media_html(html: str) -> str:
    """Keep media inert until its slide becomes the active presentation page."""
    deferred = _SLIDE_MEDIA_SRC_RE.sub(r"\1 data-vaultpub-src=", html)
    return _SLIDE_AV_TAG_RE.sub(r'<\1 preload="none"', deferred)


def slides_page_template(
    title: str,
    slides_html: str,
    options: SlideOptions,
    return_url: str,
    return_label: str,
    split_override: str | None = None,
    slide_manifest: list[dict[str, object]] | None = None,
) -> str:
    """Return the standalone ASGI presentation document."""
    config_json = json.dumps(options.reveal_config()).replace("<", "\\u003c").replace(">", "\\u003e")
    settings_json = json.dumps(options.client_config(split_override)).replace("<", "\\u003c").replace(">", "\\u003e")
    manifest_json = json.dumps(slide_manifest or []).replace("<", "\\u003c").replace(">", "\\u003e")
    multi_note_attr = ' data-vaultpub-multi-note="true"' if slide_manifest is not None else ""
    single_layout_attr = ' data-slide-layout="single"' if (split_override or options.split) == "single" else ""
    print_notice = (
        '<p class="slides-print-notice">Multi-note Slide View cannot be printed as one document.</p>'
        if slide_manifest is not None
        else ""
    )
    return f"""\
<!DOCTYPE html>
<html lang="en" class="theme-{escape(options.theme, quote=True)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <script src="/static/vaultpub/slides-boot.js"></script>
  <link rel="stylesheet" href="/static/vaultpub/common.css">
  <link rel="stylesheet" href="/static/vaultpub/slides.css">
</head>
<body class="vaultpub-slides"
      data-return-url="{escape(return_url, quote=True)}"
      data-return-label="{escape(return_label, quote=True)}"{multi_note_attr}{single_layout_attr}>
  <div class="reveal"><div class="slides">{slides_html}</div></div>
  {print_notice}
  <script id="vaultpub-slides-config" type="application/json">{config_json}</script>
  <script id="vaultpub-slide-settings" type="application/json">{settings_json}</script>
  <script id="vaultpub-slide-manifest" type="application/json">{manifest_json}</script>
  <script type="module" src="/static/vaultpub/slides.js"></script>
</body>
</html>"""


def base_page_template(
    content_html: str,
    nav_html: str = "",
    head_html: str = "",
    config: object | None = None,
    sidebar_right_html: str = "",
    sidebar_right_title: str = "Page",
    graph_html: str = "",
    topbar_context_html: str = "",
    vault_slides_url: str | None = None,
    slide_scopes: list[dict[str, str]] | None = None,
    order_editor_url: str | None = None,
) -> str:
    """Wrap content in a basic HTML page template."""
    site_name = getattr(config, "site_name", "vaultpub") if config else "vaultpub"
    site_logo = getattr(config, "site_logo", None) if config else None
    realtime = "true" if (config and getattr(config, "realtime", True)) else "false"
    logo_html = f'<img src="{site_logo}" alt="{site_name}" class="site-logo">' if site_logo else ""
    search_trigger = '<button class="search-trigger" data-action="search" aria-label="Search">Search (Ctrl+K)</button>'
    vault_slides_attr = f' data-vault-slides-url="{escape(vault_slides_url, quote=True)}"' if vault_slides_url else ""
    order_editor_attr = (
        f' data-order-editor-url="{escape(order_editor_url, quote=True)}"' if order_editor_url else ""
    )
    scopes_json = ""
    if slide_scopes:
        scope_data = json.dumps(slide_scopes).replace("<", "\\u003c").replace(">", "\\u003e")
        scopes_json = f'<script id="vaultpub-slide-scopes" type="application/json">{scope_data}</script>'
    right_sidebar = sidebar_right_html + graph_html
    right_sidebar_title_html = escape(sidebar_right_title)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_html}
  <script src="/static/vaultpub/boot.js"></script>
  <link rel="stylesheet" href="/static/vaultpub/common.css">
  <link rel="stylesheet" href="/static/vaultpub/app.css">
</head>
<body data-realtime="{realtime}"{vault_slides_attr}{order_editor_attr}>
  <header class="top-bar">
    <button id="mobile-menu-btn" class="mobile-menu-btn" aria-label="Toggle navigation">&#9776;</button>
    {logo_html}
    <span class="site-name">{site_name}</span>
    {topbar_context_html}
    <div class="topbar-actions">
      {search_trigger}
    </div>
  </header>
  <div class="app-layout">
    <aside class="sidebar-left">
      <div class="sidebar-left-sticky">
        <div class="sidebar-top">
          {logo_html}
          <span class="site-name">{site_name}</span>
        </div>
        <div class="sidebar-header">
          <div class="sidebar-header-actions">
          <button class="sidebar-action" type="button" data-nav-tree-action="expand"
                  title="Expand all" aria-label="Expand all">+</button>
          <button class="sidebar-action" type="button" data-nav-tree-action="collapse"
                  title="Collapse all" aria-label="Collapse all">&minus;</button>
          <select class="sidebar-action nav-sort-select" data-nav-sort aria-label="Sort navigation"
                  title="Sort navigation">
            <option value="predefined">Order</option>
            <option value="name-asc">Name A–Z</option>
            <option value="name-desc">Name Z–A</option>
            <option value="created-desc">Created newest</option>
            <option value="created-asc">Created oldest</option>
            <option value="modified-desc" selected>Modified newest</option>
            <option value="modified-asc">Modified oldest</option>
          </select>
          <button class="sidebar-action" type="button" data-nav-folder-layout="top"
                  title="Move folders to top bar" aria-label="Move folders to top bar" aria-pressed="false">&#8657;</button>
            <button class="sidebar-toggle" type="button" data-sidebar-toggle="left"
                    aria-label="Hide navigation">&lt;</button>
          </div>
        </div>
      </div>
      <nav class="file-tree">{nav_html}</nav>
    </aside>
    <main class="content">
      {content_html}
    </main>
    <aside class="sidebar-right">
      <div class="sidebar-top">
        {search_trigger}
      </div>
      <div class="sidebar-header">
        <div class="sidebar-title">{right_sidebar_title_html}</div>
        <button class="sidebar-toggle" type="button" data-sidebar-toggle="right"
                aria-label="Hide page sidebar">&gt;</button>
      </div>
      {right_sidebar}
    </aside>
  </div>
  {scopes_json}
  <script type="module" src="/static/vaultpub/app.js"></script>
</body>
</html>"""


def order_editor_page_html(
    data_url: str,
    save_url: str,
    initial_directory: str,
    csrf_token: str = "",
) -> str:
    """Render the live-only navigation ordering workspace."""
    return f"""\
<article class="order-editor" data-order-editor
         data-order-data-url="{escape(data_url, quote=True)}"
         data-order-save-url="{escape(save_url, quote=True)}"
         data-initial-directory="{escape(initial_directory, quote=True)}"
         data-csrf-token="{escape(csrf_token, quote=True)}">
  <header class="order-editor-header">
    <div><h1>Custom order</h1><p data-order-editor-path></p></div>
    <div class="order-editor-actions">
      <button type="button" class="order-editor-icon-button" data-order-reset title="Use default order" aria-label="Use default order"><i data-lucide="rotate-ccw" aria-hidden="true"></i></button>
      <button type="button" class="order-editor-save" data-order-save><i data-lucide="save" aria-hidden="true"></i><span>Save order</span></button>
    </div>
  </header>
  <label class="order-editor-folder">Folder
    <input type="search" list="order-editor-folders" data-order-directory aria-label="Folder">
    <datalist id="order-editor-folders"></datalist>
  </label>
  <p class="order-editor-status" data-order-status role="status" aria-live="polite"></p>
  <section class="order-editor-section" data-order-pinned-section hidden>
    <h2>Pinned</h2><ul class="order-editor-list" data-order-pinned></ul>
  </section>
  <section class="order-editor-section">
    <h2>Folders</h2><ul class="order-editor-list" data-order-folders></ul>
  </section>
  <section class="order-editor-section">
    <h2>Files</h2><ul class="order-editor-list" data-order-files></ul>
  </section>
</article>"""


def find_nav_directory(node: NavNode | None, dir_path: str) -> NavNode | None:
    """Return the nav directory node for a relative directory path."""
    if node is None:
        return None
    normalized = dir_path.strip("/")
    if normalized in ("", "."):
        return node
    if node.is_dir and node.path == normalized:
        return node
    for child in node.children:
        if child.is_dir:
            found = find_nav_directory(child, normalized)
            if found is not None:
                return found
    return None


def directory_sibling_files_html(
    nav_tree: NavNode | None,
    directory: NavNode,
    url_transform: Callable[[str], str] | None = None,
) -> str:
    """Render links to files alongside the current directory in its parent directory."""
    if nav_tree is None:
        return ""

    parent_path = PurePosixPath(directory.path).parent.as_posix()
    parent_node = find_nav_directory(nav_tree, parent_path)
    if parent_node is None:
        return ""

    sibling_files = [child for child in parent_node.children if not child.is_dir and not child.nav_hidden]
    if not sibling_files:
        return """\
<nav class="directory-context-nav">
  <h3>Same Directory</h3>
  <p class="directory-context-empty">No files in this directory.</p>
</nav>"""

    items = "".join(
        f'<li{_nav_sort_attrs(child)}><a href="{escape(_transform_url(child.url, url_transform), quote=True)}">'
        f"{_star_html(child)}{escape(child.label)}</a></li>"
        for child in sibling_files
    )
    return f"""\
<nav class="directory-context-nav">
  <h3>Same Directory</h3>
  <ul data-nav-sort-list>{items}</ul>
</nav>"""


def directory_page_html(
    node: NavNode,
    current_path: str,
    content_previews: dict[str, str] | None = None,
    url_transform: Callable[[str], str] | None = None,
) -> str:
    """Render a directory landing page as a single-column list of cards."""
    items: list[str] = []
    previews = content_previews or {}
    visible_children = [child for child in node.children if not child.nav_hidden]
    for child in visible_children:
        child_url = _transform_url(child.url, url_transform)
        child_title = f"{child.label}/" if child.is_dir else child.label
        item_class = "directory-list-item is-folder" if child.is_dir else "directory-list-item is-file"
        if child.is_dir:
            child_detail_html = '<span class="directory-list-meta">Folder</span>'
        else:
            preview = previews.get(child.path, "")
            child_detail_html = (
                f'<span class="directory-list-preview">{escape(preview)}</span>'
                if preview
                else ""
            )
        items.append(
            f"<li{_nav_sort_attrs(child)}>"
            f'<a href="{escape(child_url, quote=True)}" class="{item_class}">'
            f'<span class="directory-list-title">{_star_html(child)}{_icon_html(child)}{escape(child_title)}</span>'
            f"{child_detail_html}"
            "</a>"
            "</li>"
        )

    directory_title = "Home" if node.path in (".", "") else f"{node.label}/"
    item_count = f"{len(visible_children)} item" if len(visible_children) == 1 else f"{len(visible_children)} items"
    empty_state = '<p class="directory-empty">This folder has no published children.</p>' if not items else ""
    list_html = f'<ul class="directory-list" data-nav-sort-list>{"".join(items)}</ul>' if items else ""
    description_html = f"<p>{escape(node.description)}</p>" if node.description else ""
    current_attr = escape(current_path, quote=True)
    return f"""\
<article class="directory-page" data-current-path="{current_attr}">
  <header class="directory-page-header">
    <h1>{escape(directory_title)}</h1>
    <p>{escape(item_count)}</p>
    {description_html}
  </header>
  {empty_state}
  {list_html}
</article>"""


def nav_tree_html(
    node: object,
    path: tuple[str, ...] = (),
    url_transform: Callable[[str], str] | None = None,
) -> str:
    """Render a nav tree node to HTML."""
    if node is None:
        return ""

    label = str(getattr(node, "label", "root"))
    url = getattr(node, "url", "/")
    is_dir = getattr(node, "is_dir", False)
    children = getattr(node, "children", [])
    node_path = path if label == "/" and not path else (*path, label)

    if label == "/" and is_dir and not path:
        return "".join(nav_tree_html(c, node_path, url_transform) for c in children)

    if bool(getattr(node, "nav_hidden", False)):
        return ""

    if is_dir:
        visible_children = [child for child in children if not bool(getattr(child, "nav_hidden", False))]
        if not visible_children:
            return ""
        child_html = "".join(nav_tree_html(c, node_path, url_transform) for c in visible_children)
        nav_key = escape("/".join(node_path) or "/", quote=True)
        folder_url = escape(_transform_url(str(url), url_transform), quote=True)
        folder_path = escape(str(getattr(node, "path", "")), quote=True)
        open_attr = "" if bool(getattr(node, "collapsed", False)) else " open"
        return (
            f'<li{_nav_sort_attrs(node)}><details{open_attr} data-nav-key="{nav_key}">'
            f'<summary class="nav-folder-summary" data-folder-path="{folder_path}">'
            f'<a href="{folder_url}" class="nav-folder-link">{_star_html(node)}{_icon_html(node)}{escape(label)}/</a>'
            '<button type="button" class="nav-folder-toggle" aria-label="Toggle folder">'
            '<span class="nav-folder-toggle-icon" aria-hidden="true"></span>'
            "</button>"
            f"</summary><ul data-nav-sort-list>{child_html}</ul></details></li>"
        )
    else:
        file_url = escape(_transform_url(str(url), url_transform), quote=True)
        return (
            f'<li{_nav_sort_attrs(node)}><a href="{file_url}" class="internal-link">'
            f"{_star_html(node)}{_icon_html(node)}{escape(label)}</a></li>"
        )


def _nav_sort_attrs(node: object) -> str:
    raw_label = str(getattr(node, "raw_label", "") or getattr(node, "label", ""))
    kind = "folder" if bool(getattr(node, "is_dir", False)) else "file"
    created = int(getattr(node, "created_ns", 0) or 0)
    modified = int(getattr(node, "modified_ns", 0) or 0)
    starred = "true" if bool(getattr(node, "starred", False)) else "false"
    predefined_order = "true" if bool(getattr(node, "predefined_order", False)) else "false"
    return (
        f' data-nav-sort-item data-nav-name="{escape(raw_label, quote=True)}"'
        f' data-nav-kind="{kind}" data-nav-created="{created}"'
        f' data-nav-modified="{modified}" data-nav-starred="{starred}"'
        f' data-nav-predefined-order="{predefined_order}"'
    )


def _star_html(node: object) -> str:
    if not bool(getattr(node, "starred", False)):
        return ""
    return '<span class="nav-star" aria-label="Starred" title="Starred">★</span>'


def _icon_html(node: object) -> str:
    icon = str(getattr(node, "icon", ""))
    return f'<span class="nav-icon" aria-hidden="true">{escape(icon)}</span>' if icon else ""


def _transform_url(url: str, url_transform: Callable[[str], str] | None) -> str:
    return url_transform(url) if url_transform is not None else url
