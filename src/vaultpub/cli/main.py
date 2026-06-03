"""vaultpub CLI entry point.

Provides: serve, build, index, doctor, init
"""
from __future__ import annotations

import typer

app = typer.Typer(name="vaultpub", help="Publish a local Obsidian vault as a web site")


@app.callback()
def callback() -> None:
    """vaultpub — Obsidian vault publisher."""


@app.command()
def serve(
    vault: str = typer.Option(..., "--vault", help="Path to Obsidian vault"),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8008, "--port", help="Bind port"),
    home: str | None = typer.Option(None, "--home", help="Home file (e.g. README)"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on changes"),
    config: str | None = typer.Option(None, "--config", help="Path to config YAML"),
) -> None:
    """Start the vaultpub web server."""
    from pathlib import Path

    import uvicorn

    from vaultpub.core.config import load_config
    from vaultpub.web import create_app

    cfg = load_config(vault_path=Path(vault), yaml_path=config)
    if home:
        cfg = cfg.__class__(**{**cfg.__dict__, "home_file": home})

    asgi_app = create_app(cfg)
    uvicorn.run(asgi_app, host=host, port=port, reload=reload)  # type: ignore[arg-type]


@app.command()
def build(
    vault: str = typer.Option(..., "--vault", help="Path to Obsidian vault"),
    out: str = typer.Option("./public", "--out", help="Output directory"),
    clean: bool = typer.Option(False, "--clean", help="Clean output dir before build"),
    base_url: str | None = typer.Option(None, "--base-url", help="Base URL for generated links"),
    config: str | None = typer.Option(None, "--config", help="Path to config YAML"),
) -> None:
    """Build a static site from the vault."""
    from pathlib import Path

    from vaultpub.core.config import load_config
    from vaultpub.export import StaticSiteBuilder

    cfg = load_config(vault_path=Path(vault), yaml_path=config)
    if base_url:
        cfg = cfg.__class__(**{**cfg.__dict__, "site_url": base_url})

    builder = StaticSiteBuilder(cfg)
    result = builder.build(out_dir=Path(out), clean=clean)
    print(f"Built {result.pages_written} pages to {out}")


@app.command()
def index(
    vault: str = typer.Option(..., "--vault", help="Path to Obsidian vault"),
    json_path: str = typer.Option("./index.json", "--json", help="Output JSON path"),
    config: str | None = typer.Option(None, "--config", help="Path to config YAML"),
) -> None:
    """Export the vault index as JSON."""
    import json
    from pathlib import Path

    from vaultpub.core.config import load_config
    from vaultpub.core.index.indexer import VaultIndexer

    cfg = load_config(vault_path=Path(vault), yaml_path=config)
    indexer = VaultIndexer(cfg)
    vault_index = indexer.build()

    serializable = {
        "notes": {k: _note_to_dict(v) for k, v in vault_index.notes_by_id.items()},
        "attachments": {k: _att_to_dict(v) for k, v in vault_index.attachments_by_path.items()},
        "tags": {k: list(v) for k, v in vault_index.tags.items()},
        "permalinks": vault_index.permalinks,
        "redirects": vault_index.redirects,
    }
    Path(json_path).write_text(json.dumps(serializable, indent=2, ensure_ascii=False))
    print(f"Index written to {json_path}")


@app.command()
def doctor(
    vault: str = typer.Option(..., "--vault", help="Path to Obsidian vault"),
    config: str | None = typer.Option(None, "--config", help="Path to config YAML"),
) -> None:
    """Diagnose vault issues: broken links, duplicates, etc."""
    from pathlib import Path

    from vaultpub.core.config import load_config
    from vaultpub.core.index.indexer import VaultIndexer

    cfg = load_config(vault_path=Path(vault), yaml_path=config)
    indexer = VaultIndexer(cfg)
    vault_index = indexer.build()

    broken = []
    for note in vault_index.notes_by_id.values():
        for link in note.outgoing_links:
            if not link.is_resolved:
                broken.append(f"  {note.rel_path} -> [[{link.target_text}]] ({link.reason_unresolved})")

    dupes = []
    for stem, ids in vault_index.notes_by_stem.items():
        if len(ids) > 1:
            dupes.append(f"  {stem}: {len(ids)} notes")

    print(f"Notes: {len(vault_index.notes_by_id)}")
    print(f"Attachments: {len(vault_index.attachments_by_path)}")
    print(f"Tags: {len(vault_index.tags)}")
    print(f"Permalinks: {len(vault_index.permalinks)}")
    print()
    if broken:
        print(f"Broken links ({len(broken)}):")
        for b in broken:
            print(b)
    else:
        print("No broken links.")
    print()
    if dupes:
        print(f"Duplicate stems ({len(dupes)}):")
        for d in dupes:
            print(d)
    else:
        print("No duplicate stems.")


@app.command()
def init(
    vault: str = typer.Option(..., "--vault", help="Path to Obsidian vault"),
) -> None:
    """Create a default .vaultpub.yml in the vault directory."""
    from pathlib import Path

    config_path = Path(vault) / ".vaultpub.yml"
    if config_path.exists():
        print(f"{config_path} already exists, skipping.")
        return
    config_path.write_text("""\
# vaultpub configuration
# See: https://github.com/vaultpub/vaultpub

vault_path: .
site:
  name: My Knowledge Base
  title: My Knowledge Base
  description: Personal notes

publish:
  mode: publish_false_hides
  exclude_folders:
    - .obsidian
    - .git
    - private
    - trash
  exclude_globs:
    - "**/*.draft.md"

rendering:
  strict_line_breaks: true
  html_safe_mode: true
  enable_mermaid: true
  enable_math: true
  enable_callouts: true

features:
  navigation: true
  search: true
  graph: true
  toc: true
  backlinks: true
  hover_preview: true
  theme_toggle: true

realtime:
  enabled: true
  transport: auto
  debounce_ms: 150
""")
    print(f"Created {config_path}")


def _note_to_dict(note: object) -> dict:
    """Serialize a NoteRecord to a JSON-safe dict."""
    return {
        "id": getattr(note, "id", ""),
        "rel_path": str(getattr(note, "rel_path", "")),
        "url_path": getattr(note, "url_path", ""),
        "title": getattr(note, "title", ""),
        "stem": getattr(note, "stem", ""),
        "aliases": list(getattr(note, "aliases", [])),
        "tags": list(getattr(note, "tags", [])),
        "headings": [{"level": h.level, "text": h.text, "slug": h.slug} for h in getattr(note, "headings", [])],
        "excerpt": getattr(note, "excerpt", ""),
        "outgoing_links": [
            {
                "raw": link.raw,
                "target_text": link.target_text,
                "target_id": link.target_id,
                "is_embed": link.is_embed,
                "is_resolved": link.is_resolved,
            }
            for link in getattr(note, "outgoing_links", [])
        ],
    }


def _att_to_dict(att: object) -> dict:
    return {
        "id": getattr(att, "id", ""),
        "rel_path": str(getattr(att, "rel_path", "")),
        "url_path": getattr(att, "url_path", ""),
        "mime_type": getattr(att, "mime_type", ""),
        "size": getattr(att, "size", 0),
    }
