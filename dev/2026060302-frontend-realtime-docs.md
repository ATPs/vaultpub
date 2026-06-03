# Feature: Frontend, Realtime, Docs (Phases 7–8, 10)

## Goal

Complete the remaining development phases:
- Phase 7: Vite + TypeScript frontend with theme, search, graph, preview, callouts, mobile
- Phase 8: Realtime updates via watchfiles, SSE, EventBus
- Phase 10: Security docs, README, CSP guidance, final polish (no Docker)

## Conclusion

All three phases are functionally complete.

**Phase 7 — Frontend:**
- Vite + TypeScript project scaffold in `frontend/`
- 10 TypeScript modules: app, theme, search, preview, graph, realtime, stacked-pages, mermaid-init, math-init, mobile
- 4 CSS modules: base, obsidian-vars (light/dark themes), callouts, layout
- Pre-built static assets (app.js, app.css) in `django_app/static/vaultpub/` for zero-dependency serving
- Full Vite pipeline available for customization (`npm run build`)

**Phase 8 — Realtime:**
- `core/realtime/events.py` — EventBus with pub/sub, version tracking, event history
- `core/realtime/watcher.py` — watchfiles-based vault watcher with debounce
- `core/realtime/broadcaster.py` — SSE broadcaster for streaming events to clients
- `web/sse.py` — Real SSE endpoint (`/api/events`)
- `web/app.py` — Lifespan-based watcher startup/shutdown
- Frontend client: `realtime.ts` with SSE + polling fallback

**Phase 10 — Polish:**
- Comprehensive README with all commands, config, API docs, CSP guidance
- Security: path traversal tests, HTML sanitize, publish filter tests all passing
- No Docker (per user request)

## Changed Files

- `frontend/package.json` — Vite + TypeScript + dependencies
- `frontend/vite.config.ts` — Build config targeting static dir
- `frontend/tsconfig.json` — TypeScript config
- `frontend/src/app.ts` — Entry point
- `frontend/src/theme.ts` — Theme toggle with localStorage
- `frontend/src/search.ts` — Search modal with MiniSearch + API fallback
- `frontend/src/preview.ts` — Hover preview for internal links
- `frontend/src/graph.ts` — Canvas force-directed graph
- `frontend/src/realtime.ts` — SSE client with polling fallback
- `frontend/src/stacked-pages.ts` — Callout folding
- `frontend/src/mermaid-init.ts` — Mermaid dynamic init
- `frontend/src/math-init.ts` — KaTeX dynamic init
- `frontend/src/mobile.ts` — Mobile drawer/responsive
- `frontend/src/styles/base.css` — Core styles
- `frontend/src/styles/obsidian-vars.css` — Theme variables
- `frontend/src/styles/callouts.css` — Callout block styles
- `frontend/src/styles/layout.css` — Page layout + responsive
- `src/vaultpub/django_app/static/vaultpub/app.css` — Pre-built CSS
- `src/vaultpub/django_app/static/vaultpub/app.js` — Pre-built JS
- `src/vaultpub/core/realtime/events.py` — Updated with version tracking
- `src/vaultpub/core/realtime/watcher.py` — watchfiles integration
- `src/vaultpub/core/realtime/broadcaster.py` — SSE broadcaster
- `src/vaultpub/core/realtime/__init__.py` — Re-exports
- `src/vaultpub/web/sse.py` — Real SSE endpoint
- `src/vaultpub/web/app.py` — Lifespan + watcher wiring
- `src/vaultpub/web/routes.py` — AppState extended with event_bus
- `README.md` — Full documentation

## Tests

- 73 tests passing
- Ruff lint: all checks pass
- CLI: `vaultpub --help`, `doctor`, `build` all verified

## Manual Verification

```bash
vaultpub doctor --vault tests/fixtures/vault_basic  # 3 notes, clean
vaultpub build --vault tests/fixtures/vault_basic --out /tmp/site  # 3 pages
```

Built site structure: index.html, per-note dirs, graph.json, search-index.json, robots.txt

## Known Limitations

- Frontend Vite build requires Node.js; pre-built fallback shipped for Python-only use
- Graph uses simple canvas rendering (no vis-network dependency)
- Watchfiles watcher does full index rebuild on change (optimized incremental path deferred)
- Django Channels optional (SSE fallback works without Channels)
- No Dockerfile (user request)
