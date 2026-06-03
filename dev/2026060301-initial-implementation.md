# Feature: Initial Implementation (Phases 0–6, 9)

## Goal

Build the initial working version of vaultpub covering:
- Project skeleton with CLI, linting, testing (Phase 0)
- Configuration, path safety, vault scanning, publish filtering (Phase 1)
- Markdown rendering and wikilink resolution (Phase 2)
- VaultIndex with backlinks, tags, search, graph (Phase 3)
- Standalone ASGI web app with Starlette (Phase 4)
- Django reusable app (Phase 5)
- Obsidian syntax: embeds, callouts, mermaid/math placeholders (Phase 6)
- Static site export (Phase 9)

## Conclusion

All above phases are functionally complete. 73 tests pass, linting is clean, CLI works end-to-end.

**Implemented modules:**
- `vaultpub.core` — config, paths, scanner, models, frontmatter, parser/*, indexer, renderer, sanitize, seo, templates, security, exceptions, realtime, export (static_builder)
- `vaultpub.web` — Starlette app, routes (page, attachment, api_page, api_search, api_graph)
- `vaultpub.django_app` — AppConfig, conf (settings bridge), urls, views, templates, template_tags
- `vaultpub.cli` — Typer commands: serve, build, index, doctor, init
- `vaultpub.export` — StaticSiteBuilder with pretty URLs, search-index, graph, sitemap, robots

**Fixture vaults:** vault_basic, vault_links, vault_obsidian_syntax, vault_security, vault_publish_filters

## Tests

- 73 tests passing (unit + integration + django)
- Lint: `ruff check` clean
- CLI verified: `--help`, `doctor`, `index`, `build` commands work

## Manual Verification

```bash
vaultpub --help              # all 5 commands shown
vaultpub doctor --vault tests/fixtures/vault_basic  # 3 notes, no errors
vaultpub index --vault tests/fixtures/vault_basic --json /tmp/index.json  # JSON written
vaultpub build --vault tests/fixtures/vault_basic --out /tmp/site --clean  # 3 pages built
```

Built site output: index.html, per-note index.html, graph.json, search-index.json, robots.txt

## Known Limitations

- Frontend (Phase 7): No Vite/TypeScript yet; frontend assets are minimal
- Realtime (Phase 8): SSE stub exists but no watchfiles integration
- MSS in Django: Starlette deprecation warning for httpx (needs httpx2)
- Security hardening (Phase 10): CSP docs, Dockerfile, CI not yet done
- SQLite FTS not implemented (v0.1 target is client-side search only)
- Canvas preview not implemented
- `publish.css`/`publish.js` trusted mode not implemented
