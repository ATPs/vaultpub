"""HTML templates for page layout."""
from __future__ import annotations

from html import escape
from pathlib import PurePosixPath

from vaultpub.core.models import GraphData, Heading, NoteRecord, TextPageRecord


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


def _breadcrumbs_html(rel_path: PurePosixPath, home_url: str = "/") -> str:
    segments = [f'<a href="{escape(home_url, quote=True)}" class="topbar-breadcrumb-link">Home</a>']
    parts = list(rel_path.parts)

    for part in parts[:-1]:
        segments.append('<span class="topbar-breadcrumb-sep">/</span>')
        segments.append(f'<span class="topbar-breadcrumb-segment">{escape(part)}</span>')

    if parts:
        segments.append('<span class="topbar-breadcrumb-sep">/</span>')
        segments.append(f'<span class="topbar-breadcrumb-current">{escape(parts[-1])}</span>')

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


def topbar_context_html_for_note(note: NoteRecord, home_url: str = "/") -> str:
    heading = _preferred_heading(note)
    heading_href = f' href="#{escape(heading.slug, quote=True)}"' if heading is not None else ""
    heading_hidden = "" if heading is not None else " hidden"
    heading_text = escape(heading.text) if heading is not None else ""

    return f"""\
<div class="topbar-context topbar-context-note" data-topbar-context="note">
  <nav class="topbar-breadcrumbs" aria-label="Current location">
    {_breadcrumbs_html(note.rel_path, home_url)}
  </nav>
  <a class="topbar-current-heading" data-current-heading aria-live="polite"{heading_href}{heading_hidden}>{heading_text}</a>
</div>"""


def topbar_context_html_for_text_page(text_page: TextPageRecord, home_url: str = "/") -> str:
    return f"""\
<div class="topbar-context topbar-context-code" data-topbar-context="code">
  <nav class="topbar-breadcrumbs" aria-label="Current location">
    {_breadcrumbs_html(text_page.rel_path, home_url)}
  </nav>
  <div class="topbar-code-tools">
    <span class="topbar-code-meta">{escape(_language_label(text_page))} &middot; {_format_size(text_page.size)}</span>
    <button class="topbar-code-btn" type="button" data-code-action="copy-path"
            data-code-path="{escape(text_page.rel_path.as_posix(), quote=True)}">Copy path</button>
    <button class="topbar-code-btn" type="button" data-code-action="toggle-wrap" aria-pressed="false">Wrap</button>
  </div>
</div>"""


def base_page_template(
    content_html: str,
    nav_html: str = "",
    head_html: str = "",
    config: object | None = None,
    sidebar_right_html: str = "",
    graph_html: str = "",
    topbar_context_html: str = "",
) -> str:
    """Wrap content in a basic HTML page template."""
    site_name = getattr(config, "site_name", "vaultpub") if config else "vaultpub"
    site_logo = getattr(config, "site_logo", None) if config else None
    realtime = "true" if (config and getattr(config, "realtime", True)) else "false"
    logo_html = f'<img src="{site_logo}" alt="{site_name}" class="site-logo">' if site_logo else ""
    search_trigger = '<button class="search-trigger" data-action="search" aria-label="Search">Search (Ctrl+K)</button>'
    right_sidebar = sidebar_right_html + graph_html

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_html}
  <link rel="stylesheet" href="/static/vaultpub/app.css">
</head>
<body data-realtime="{realtime}">
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
      <div class="sidebar-top">
        {logo_html}
        <span class="site-name">{site_name}</span>
      </div>
      <div class="sidebar-header">
        <div class="sidebar-title">Navigation</div>
        <button class="sidebar-toggle" type="button" data-sidebar-toggle="left"
                aria-label="Hide navigation">&lt;</button>
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
        <div class="sidebar-title">Page</div>
        <button class="sidebar-toggle" type="button" data-sidebar-toggle="right"
                aria-label="Hide page sidebar">&gt;</button>
      </div>
      {right_sidebar}
    </aside>
  </div>
  <script type="module" src="/static/vaultpub/app.js"></script>
</body>
</html>"""


def nav_tree_html(node: object, path: tuple[str, ...] = ()) -> str:
    """Render a nav tree node to HTML."""
    if node is None:
        return ""

    label = str(getattr(node, "label", "root"))
    url = getattr(node, "url", "/")
    is_dir = getattr(node, "is_dir", False)
    children = getattr(node, "children", [])
    node_path = path if label == "/" and not path else (*path, label)

    if label == "/" and is_dir and not path:
        return "".join(nav_tree_html(c, node_path) for c in children)

    if is_dir:
        if not children:
            return ""
        child_html = "".join(nav_tree_html(c, node_path) for c in children)
        nav_key = escape("/".join(node_path) or "/", quote=True)
        return (
            f'<li><details open data-nav-key="{nav_key}">'
            f"<summary>{escape(label)}</summary><ul>{child_html}</ul></details></li>"
        )
    else:
        return f'<li><a href="{escape(str(url), quote=True)}" class="internal-link">{escape(label)}</a></li>'
