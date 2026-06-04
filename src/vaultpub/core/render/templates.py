"""HTML templates for page layout."""
from __future__ import annotations

from html import escape


def base_page_template(
    content_html: str,
    nav_html: str = "",
    head_html: str = "",
    config: object | None = None,
    sidebar_right_html: str = "",
) -> str:
    """Wrap content in a basic HTML page template."""
    site_name = getattr(config, "site_name", "vaultpub") if config else "vaultpub"
    site_logo = getattr(config, "site_logo", None) if config else None
    realtime = "true" if (config and getattr(config, "realtime", True)) else "false"
    show_graph = config and (getattr(config, "show_graph", True) or getattr(config, "show_local_graph", True))

    logo_html = f'<img src="{site_logo}" alt="{site_name}" class="site-logo">' if site_logo else ""
    search_trigger = '<button class="search-trigger" data-action="search" aria-label="Search">Search (Ctrl+K)</button>'
    graph_container = '<div id="graph-container" class="graph-container"></div>' if show_graph else ""
    right_sidebar = sidebar_right_html + graph_container

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
    {search_trigger}
  </header>
  <div class="app-layout">
    <aside class="sidebar-left">
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
