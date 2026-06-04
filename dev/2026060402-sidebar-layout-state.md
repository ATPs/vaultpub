# Feature: sidebar layout state

## Goal

Fix `vaultpub serve` page usability issues:

- long inline paths should remain visible within the page content
- left and right sidebars should have title bars and hide/show controls
- collapsed sidebars should expose hoverable floating buttons
- left navigation directory collapse state should persist across page navigation
- serve mode should provide the same search and graph JSON URLs that the frontend requests

Verify against the reported PXD014791 page in a browser and with integration tests.

## Conclusion

Added sidebar headers and controls to the standalone and Django templates, moved standalone page TOC/backlinks into the right sidebar, added a frontend sidebar-state module, and updated CSS so long inline code wraps without creating horizontal page overflow. Added `/search-index.json` and `/graph.json` routes for serve mode to avoid static-mode fallback 404s.

Rebuilt frontend assets with Vite as ES modules and copied dynamic frontend assets during static export.

## Changed Files

- `.gitignore`
- `frontend/src/app.ts`
- `frontend/src/search.ts`
- `frontend/src/sidebar.ts`
- `frontend/src/styles/base.css`
- `frontend/src/styles/layout.css`
- `frontend/src/vite-env.d.ts`
- `frontend/vite.config.ts`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `src/vaultpub/django_app/static/vaultpub/assets/`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/web/app.py`
- `src/vaultpub/web/routes.py`
- `tests/integration/test_web_app.py`

## Tests

- `npm install --no-package-lock`
- `npm run build`
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest`

## Manual Verification

- Started a test server on `127.0.0.1:8018` with the reported vault.
- Playwright Firefox check on `/20260423processing/20260423.full_preprocessing_robustness`:
  - long reported path fits within the content column
  - no horizontal page overflow
  - right sidebar title is `Page` and TOC is present
  - collapsed sidebars show floating buttons
  - hovering floating buttons temporarily reveals the sidebars
  - `temp` directory collapse state remains closed after navigating to `/README`
  - `/search-index.json` and `/graph.json` return 200
  - console has 0 errors and 0 warnings
