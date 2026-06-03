"""HTML templates for page layout."""
from __future__ import annotations


def base_page_template(
    content_html: str,
    nav_html: str = "",
    head_html: str = "",
    config: object | None = None,
) -> str:
    """Wrap content in a basic HTML page template."""
    site_name = getattr(config, "site_name", "vaultpub") if config else "vaultpub"
    site_logo = getattr(config, "site_logo", None) if config else None
    realtime = "true" if (config and getattr(config, "realtime", True)) else "false"
    show_graph = config and (getattr(config, "show_graph", True) or getattr(config, "show_local_graph", True))
    show_theme_toggle = config and getattr(config, "show_theme_toggle", True)

    logo_html = f'<img src="{site_logo}" alt="{site_name}" class="site-logo">' if site_logo else ""
    search_trigger = '<button class="search-trigger" data-action="search" aria-label="Search">Search (Ctrl+K)</button>'
    theme_btn = '<button id="theme-toggle" class="theme-toggle-btn" aria-label="Toggle theme">🌓</button>'
    theme_toggle = theme_btn if show_theme_toggle else ""
    graph_container = '<div id="graph-container" class="graph-container"></div>' if show_graph else ""

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
    {theme_toggle}
  </header>
  <div class="app-layout">
    <aside class="sidebar-left">
      <nav class="file-tree">{nav_html}</nav>
    </aside>
    <main class="content">
      {content_html}
    </main>
    <aside class="sidebar-right">
      {graph_container}
      <div class="sidebar-toc"></div>
      <div class="sidebar-backlinks"></div>
    </aside>
  </div>
  <script src="/static/vaultpub/app.js"></script>
</body>
</html>"""


def nav_tree_html(node: object, indent: int = 0) -> str:
    """Render a nav tree node to HTML."""
    if node is None:
        return ""

    label = getattr(node, "label", "root")
    url = getattr(node, "url", "/")
    is_dir = getattr(node, "is_dir", False)
    children = getattr(node, "children", [])

    if is_dir:
        if not children:
            return ""
        child_html = "".join(nav_tree_html(c) for c in children)
        return f"<li><details open><summary>{label}</summary><ul>{child_html}</ul></details></li>"
    else:
        return f'<li><a href="{url}" class="internal-link">{label}</a></li>'
