"""StaticSiteBuilder — builds a deployable static site from a vault."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.models import NoteRecord, VaultIndex
from vaultpub.core.render.renderer import Renderer
from vaultpub.core.render.seo import build_meta_tags
from vaultpub.core.render.templates import base_page_template, nav_tree_html


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
            url_path = note.url_path.lstrip("/")
            page_dir = out_dir / url_path
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.html").write_text(page_html)
            result.pages_written += 1

        # Home page
        home_note = indexer.scanner.resolve_home(list(vault_index.notes_by_id.values()))
        if home_note:
            page_html = self._render_page(renderer, vault_index, home_note)
            (out_dir / "index.html").write_text(page_html)

        # Permalink/alias redirect pages
        for note in vault_index.notes_by_id.values():
            permalink = note.frontmatter.get("permalink")
            if permalink:
                p = "/" + str(permalink).lstrip("/")
                redirect_html = (
                    f'<meta http-equiv="refresh" content="0;url={note.url_path}">'
                    f'<a href="{note.url_path}">Redirect</a>'
                )
                pd = out_dir / p.lstrip("/")
                pd.mkdir(parents=True, exist_ok=True)
                (pd / "index.html").write_text(redirect_html)

            for alias in note.aliases:
                alias_path = "/" + alias.lstrip("/")
                redirect_html = (
                    f'<meta http-equiv="refresh" content="0;url={note.url_path}">'
                    f'<a href="{note.url_path}">Redirect</a>'
                )
                ad = out_dir / alias_path.lstrip("/")
                ad.mkdir(parents=True, exist_ok=True)
                (ad / "index.html").write_text(redirect_html)

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
            json.dumps(vault_index.search_documents, ensure_ascii=False)
        )
        graph_data = {
            "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in vault_index.graph.nodes],
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
        body_html = renderer.render_page_html(note)
        head = build_meta_tags(note, self.config)
        nav_html = ""
        if vault_index.nav_tree:
            nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree) + "</ul>"
        return base_page_template(body_html, nav_html, head, self.config)

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
                        f'<li><a href="{note.url_path}" class="internal-link">{note.title}</a></li>'
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
  <script src="/static/vaultpub/app.js"></script>
</body>
</html>"""
            (tag_dir / "index.html").write_text(tag_page)
            count += 1
        return count

    def _write_sitemap(self, out_dir: Path, vault_index: VaultIndex) -> None:
        base = (self.config.site_url or "").rstrip("/")
        urls = []
        for note in vault_index.notes_by_id.values():
            urls.append(f"  <url><loc>{base}{note.url_path}</loc></url>")
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
      <title>{note.title}</title>
      <link>{base}{note.url_path}</link>
      <description>{note.excerpt}</description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="true">{base}{note.url_path}</guid>
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
        """Copy bundled app.css and app.js into the static output."""
        static_dst = out_dir / "static" / "vaultpub"
        static_dst.mkdir(parents=True, exist_ok=True)

        pkg_static = Path(__file__).parent.parent.parent / "django_app" / "static" / "vaultpub"
        for fname in ("app.css", "app.js"):
            src = pkg_static / fname
            if src.exists():
                shutil.copy2(src, static_dst / fname)
