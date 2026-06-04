"""StaticSiteBuilder — builds a deployable static site from a vault."""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import UTC
from html import escape
from pathlib import Path, PurePosixPath

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NavNode, NoteRecord, TextPageRecord, VaultIndex
from vaultpub.core.paths import static_html_url
from vaultpub.core.render.renderer import Renderer
from vaultpub.core.render.seo import build_page_description, build_page_title
from vaultpub.core.render.templates import (
    base_page_template,
    directory_page_html,
    graph_container_html,
    nav_tree_html,
    sidebar_graph_state,
    topbar_context_html_for_directory,
    topbar_context_html_for_note,
    topbar_context_html_for_text_page,
)

_ABSOLUTE_ATTR_RE = re.compile(r'(?P<attr>\s(?:href|src)=["\'])(?P<url>/[^"\']*)(?P<quote>["\'])')


@dataclass
class BuildResult:
    pages_written: int = 0
    attachments_copied: int = 0
    tag_pages_written: int = 0
    errors: list[str] = field(default_factory=list)


class StaticSiteBuilder:
    """Builds a static HTML site from a vault."""

    def __init__(self, config: PublisherConfig) -> None:
        self.config = config

    def build(self, out_dir: Path, clean: bool = False) -> BuildResult:
        out_dir = out_dir.resolve()

        if clean and out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        indexer = VaultIndexer(self.config)
        vault_index = indexer.build()
        renderer = Renderer(self.config, vault_index)

        result = BuildResult()

        # Note pages
        for note in vault_index.notes_by_id.values():
            page_html = self._render_page(renderer, vault_index, note)
            page_path = self._output_path(out_dir, static_html_url(_note_public_url(note)))
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(page_html)
            result.pages_written += 1

        # Home page
        home_note = indexer.scanner.resolve_home(list(vault_index.notes_by_id.values()))
        if home_note:
            page_html = self._render_page(renderer, vault_index, home_note)
            (out_dir / "index.html").write_text(page_html)

        # Directory pages
        if vault_index.nav_tree:
            for directory in self._iter_directories(vault_index.nav_tree):
                if directory.path in ("", "."):
                    continue
                page_html = self._render_directory_page(vault_index, directory)
                page_path = self._output_path(out_dir, static_html_url(directory.url))
                page_path.parent.mkdir(parents=True, exist_ok=True)
                page_path.write_text(page_html)
                result.pages_written += 1

        # Text pages
        for tp in vault_index.text_pages_by_path.values():
            page_html = self._render_text_page_static(vault_index, tp)
            page_path = self._output_path(out_dir, static_html_url(tp.url_path))
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(page_html)
            result.pages_written += 1

        # Tag pages
        result.tag_pages_written = self._write_tag_pages(out_dir, vault_index, renderer)

        # Attachments
        assets_dir = out_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, _att in vault_index.attachments_by_path.items():
            src = self.config.vault_path / rel_path
            if src.exists():
                dst = assets_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                result.attachments_copied += 1

        # Data files
        (out_dir / "search-index.json").write_text(
            json.dumps(self._build_static_search_documents(vault_index), ensure_ascii=False)
        )
        graph_data = {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "group": n.group,
                    "url": self._static_link(n.url) if n.url else n.url,
                }
                for n in vault_index.graph.nodes
            ],
            "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in vault_index.graph.edges],
        }
        (out_dir / "graph.json").write_text(json.dumps(graph_data))

        # Static assets
        self._copy_frontend_assets(out_dir)

        # publish.css from vault root (if present)
        publish_css = self.config.vault_path / "publish.css"
        if publish_css.exists():
            static_dir = out_dir / "static" / "vaultpub"
            static_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(publish_css, static_dir / "publish.css")

        # SEO files
        if self.config.site_url:
            self._write_sitemap(out_dir, vault_index)
        else:
            result.errors.append("No site_url configured: skipping sitemap.xml")
        self._write_rss(out_dir, vault_index)
        self._write_robots(out_dir)

        return result

    def _render_page(self, renderer: Renderer, vault_index: VaultIndex, note: NoteRecord) -> str:
        body_html = renderer.render_article_html(note)
        body_html = self._rewrite_page_urls(body_html)
        toc_html = renderer.render_toc_html(note) if self.config.show_toc else ""
        backlinks_html = renderer.render_backlinks_html(note) if self.config.show_backlinks else ""
        backlinks_html = self._rewrite_page_urls(backlinks_html)
        sidebar_right_html = toc_html + backlinks_html
        show_graph, graph_note_id = sidebar_graph_state(self.config, vault_index.graph, note)
        graph_html = graph_container_html(show_graph, graph_note_id)
        head = self._build_note_head(note)
        nav_html = ""
        if vault_index.nav_tree:
            nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree, url_transform=static_html_url) + "</ul>"
        topbar_context_html = topbar_context_html_for_note(note, home_url=static_html_url("/"))
        return base_page_template(
            body_html.replace(
                f'data-note-path="{escape(note.url_path, quote=True)}"',
                f'data-note-path="{escape(static_html_url(note.url_path), quote=True)}"',
            ).replace(
                f'data-current-path="{escape(note.url_path, quote=True)}"',
                f'data-current-path="{escape(static_html_url(note.url_path), quote=True)}"',
            ),
            nav_html,
            head,
            self.config,
            sidebar_right_html,
            graph_html,
            topbar_context_html=topbar_context_html,
        )

    def _render_directory_page(self, vault_index: VaultIndex, directory: NavNode) -> str:
        body_html = directory_page_html(
            directory,
            current_path=static_html_url(directory.url),
            url_transform=static_html_url,
        )
        nav_html = ""
        if vault_index.nav_tree:
            nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree, url_transform=static_html_url) + "</ul>"
        show_graph, graph_note_id = sidebar_graph_state(self.config, vault_index.graph, None)
        graph_html = graph_container_html(show_graph, graph_note_id)
        title = "Home" if directory.path in ("", ".") else f"{directory.label}/"
        head = f"<title>{escape(title)} - {escape(self.config.site_name)}</title>"
        topbar_context_html = topbar_context_html_for_directory(
            PurePosixPath(directory.path),
            home_url=static_html_url("/"),
        )
        return base_page_template(
            body_html,
            nav_html,
            head,
            self.config,
            "",
            graph_html,
            topbar_context_html=topbar_context_html,
        )

    def _write_tag_pages(self, out_dir: Path, vault_index: VaultIndex, renderer: Renderer) -> int:
        """Generate tag pages at tags/<tag-path>/index.html."""
        count = 0
        tags_dir = out_dir / "tags"
        for tag_name, note_ids in vault_index.tags.items():
            tag_dir = tags_dir / tag_name
            tag_dir.mkdir(parents=True, exist_ok=True)

            note_items = []
            for nid in sorted(note_ids):
                note = vault_index.notes_by_id.get(nid)
                if note:
                    note_items.append(
                        '<li><a href="'
                        f'{static_html_url(_note_public_url(note))}" class="internal-link">{escape(note.rel_path.name)}'
                        "</a></li>"
                    )

            tag_page = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>#{tag_name} - {self.config.site_name}</title>
            <link rel="stylesheet" href="/static/vaultpub/app.css">
</head>
<body>
  <main class="content">
    <h1>#{tag_name}</h1>
    <p>{len(note_ids)} note(s)</p>
    <ul>{"".join(note_items)}</ul>
  </main>
  <script type="module" src="/static/vaultpub/app.js"></script>
</body>
</html>"""
            (tag_dir / "index.html").write_text(tag_page)
            count += 1
        return count

    def _write_sitemap(self, out_dir: Path, vault_index: VaultIndex) -> None:
        base = (self.config.site_url or "").rstrip("/")
        urls = []
        for note in vault_index.notes_by_id.values():
            urls.append(f"  <url><loc>{base}{static_html_url(_note_public_url(note))}</loc></url>")
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>"
        )
        (out_dir / "sitemap.xml").write_text(sitemap)

    def _write_rss(self, out_dir: Path, vault_index: VaultIndex) -> None:
        """Generate RSS feed from published notes sorted by mtime."""
        base = (self.config.site_url or "").rstrip("/")
        notes = sorted(
            vault_index.notes_by_id.values(),
            key=lambda n: n.mtime_ns,
            reverse=True,
        )

        items = []
        for note in notes[:50]:
            pub_date = ""
            from datetime import datetime

            try:
                dt = datetime.fromtimestamp(note.mtime_ns / 1e9, tz=UTC)
                pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except Exception:
                pass

            items.append(f"""\
    <item>
      <title>{escape(note.rel_path.name)}</title>
      <link>{base}{static_html_url(_note_public_url(note))}</link>
      <description>{note.excerpt}</description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="true">{base}{static_html_url(_note_public_url(note))}</guid>
    </item>""")

        rss = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{self.config.site_title or self.config.site_name}</title>
    <link>{base}/</link>
    <description>{self.config.site_description or ""}</description>
{"".join(items)}
  </channel>
</rss>"""
        (out_dir / "rss.xml").write_text(rss)

    def _write_robots(self, out_dir: Path) -> None:
        (out_dir / "robots.txt").write_text("User-agent: *\nAllow: /\n")

    def _copy_frontend_assets(self, out_dir: Path) -> None:
        """Copy bundled frontend assets into the static output."""
        static_dst = out_dir / "static" / "vaultpub"
        pkg_static = Path(__file__).parent.parent.parent / "django_app" / "static" / "vaultpub"
        if not pkg_static.exists():
            static_dst.mkdir(parents=True, exist_ok=True)
            return
        shutil.copytree(pkg_static, static_dst, dirs_exist_ok=True)

    def _render_text_page_static(self, vault_index: VaultIndex, tp: TextPageRecord) -> str:
        lang_class = f"language-{tp.language}" if tp.language else ""
        body_html = f"""\
<article class="text-page" data-page-id="{tp.id}" data-page-path="{escape(static_html_url(tp.url_path), quote=True)}" data-current-path="{escape(static_html_url(tp.url_path), quote=True)}">
  <h1>{escape(tp.title)}</h1>
  <div class="code-block">
    <pre><code class="{lang_class}">{escape(tp.raw_text)}</code></pre>
  </div>
</article>"""
        head = f"<title>{escape(tp.title)} - {escape(self.config.site_name)}</title>"
        nav_html = ""
        if vault_index.nav_tree:
            nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree, url_transform=static_html_url) + "</ul>"
        topbar_context_html = topbar_context_html_for_text_page(tp, home_url=static_html_url("/"))
        return base_page_template(
            self._rewrite_page_urls(body_html),
            nav_html,
            head,
            self.config,
            "",
            "",
            topbar_context_html=topbar_context_html,
        )

    def _build_note_head(self, note: NoteRecord) -> str:
        title = build_page_title(note, self.config)
        desc = build_page_description(note, self.config)
        url = self.config.site_url or ""
        public_path = static_html_url(_note_public_url(note))
        page_url = f"{url.rstrip('/')}{public_path}" if url else ""

        tags = [
            f"<title>{escape(title)}</title>",
            f'<meta name="description" content="{escape(desc, quote=True)}">',
        ]
        if page_url:
            tags.append(f'<link rel="canonical" href="{escape(page_url, quote=True)}">')
            tags.append(f'<meta property="og:url" content="{escape(page_url, quote=True)}">')
        tags.extend([
            f'<meta property="og:type" content="{escape(self.config.site_type, quote=True)}">',
            f'<meta property="og:title" content="{escape(title, quote=True)}">',
            f'<meta property="og:description" content="{escape(desc, quote=True)}">',
            '<meta name="twitter:card" content="summary_large_image">',
        ])
        image = note.frontmatter.get("image") or self.config.site_image
        if image:
            img_url = image if str(image).startswith("http") else f"{url.rstrip('/')}/{str(image).lstrip('/')}"
            tags.append(f'<meta property="og:image" content="{escape(img_url, quote=True)}">')
        return "\n".join(tags)

    def _rewrite_page_urls(self, html: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            url = match.group("url")
            rewritten = self._static_link(url)
            return f'{match.group("attr")}{rewritten}{match.group("quote")}'

        return _ABSOLUTE_ATTR_RE.sub(_replace, html)

    def _static_link(self, url: str) -> str:
        if url.startswith(("/assets/", "/static/")):
            return url
        if url in ("/graph.json", "/search-index.json") or url.startswith("/api/"):
            return url
        if "#" in url:
            base, anchor = url.split("#", 1)
            if not base:
                return url
            return f"{static_html_url(base)}#{anchor}"
        return static_html_url(url)

    def _iter_directories(self, node: NavNode) -> list[NavNode]:
        directories: list[NavNode] = []
        for child in node.children:
            if child.is_dir:
                directories.append(child)
                directories.extend(self._iter_directories(child))
        return directories

    def _build_static_search_documents(self, vault_index: VaultIndex) -> list[dict[str, object]]:
        docs: list[dict[str, object]] = []
        for doc in vault_index.search_documents:
            rewritten = dict(doc)
            url = rewritten.get("url")
            if isinstance(url, str):
                rewritten["url"] = self._static_link(url)
            docs.append(rewritten)
        return docs

    def _output_path(self, out_dir: Path, url: str) -> Path:
        normalized = url.lstrip("/")
        if not normalized:
            return out_dir / "index.html"
        return out_dir / normalized


def _note_public_url(note: NoteRecord) -> str:
    return note.url_path
