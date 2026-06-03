"""StaticSiteBuilder — builds a deployable static site from a vault."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.render.renderer import Renderer
from vaultpub.core.render.seo import build_meta_tags
from vaultpub.core.render.templates import base_page_template, nav_tree_html


@dataclass
class BuildResult:
    pages_written: int = 0
    attachments_copied: int = 0
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

        for note in vault_index.notes_by_id.values():
            body_html = renderer.render_page_html(note)
            head = build_meta_tags(note, self.config)
            nav_html = ""
            if vault_index.nav_tree:
                nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree) + "</ul>"
            page = base_page_template(body_html, nav_html, head, self.config)

            url_path = note.url_path.lstrip("/")
            page_dir = out_dir / url_path
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.html").write_text(page)
            result.pages_written += 1

        home_note = indexer.scanner.resolve_home(list(vault_index.notes_by_id.values()))
        if home_note:
            body_html = renderer.render_page_html(home_note)
            head = build_meta_tags(home_note, self.config)
            nav_html = ""
            if vault_index.nav_tree:
                nav_html = "<ul>" + nav_tree_html(vault_index.nav_tree) + "</ul>"
            page = base_page_template(body_html, nav_html, head, self.config)
            (out_dir / "index.html").write_text(page)

        assets_dir = out_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, _att in vault_index.attachments_by_path.items():
            src = self.config.vault_path / rel_path
            if src.exists():
                dst = assets_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                result.attachments_copied += 1

        (out_dir / "search-index.json").write_text(
            json.dumps(vault_index.search_documents, ensure_ascii=False)
        )

        graph_data = {
            "nodes": [{"id": n.id, "label": n.label, "group": n.group, "url": n.url} for n in vault_index.graph.nodes],
            "edges": [{"from": e.source, "to": e.target, "kind": e.kind} for e in vault_index.graph.edges],
        }
        (out_dir / "graph.json").write_text(json.dumps(graph_data))

        if self.config.site_url:
            self._write_sitemap(out_dir, vault_index)

        self._write_robots(out_dir)

        return result

    def _write_sitemap(self, out_dir: Path, vault_index: object) -> None:
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

    def _write_robots(self, out_dir: Path) -> None:
        (out_dir / "robots.txt").write_text("User-agent: *\nAllow: /\n")
