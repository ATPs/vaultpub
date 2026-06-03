"""HTML templates for page layout."""
from __future__ import annotations


def base_page_template(
    content_html: str,
    nav_html: str = "",
    head_html: str = "",
    config: object | None = None,
) -> str:
    """Wrap content in a basic HTML page template."""
    getattr(config, "site_name", "vaultpub") if config else "vaultpub"
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_html}
  <link rel="stylesheet" href="/static/vaultpub/app.css">
</head>
<body>
  <div class="app-layout">
    <aside class="sidebar-left">
      {nav_html}
    </aside>
    <main class="content">
      {content_html}
    </main>
    <aside class="sidebar-right">
      {{% toc %}}
      {{% backlinks %}}
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
        return f'<li><a href="{url}">{label}</a></li>'
