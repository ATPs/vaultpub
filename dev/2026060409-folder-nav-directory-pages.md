# Feature: folder nav directory pages

## Goal

Upgrade the navigation tree so folder titles navigate to folder landing pages while the arrow only expands or collapses the tree.

Unify runtime URLs so files keep their full extension and folders end with `/`.

Show file extensions in all system-generated file labels, including navigation, search, backlinks, graph labels, API titles, and page titles.

Keep static export deployable on ordinary static hosting by emitting file pages as `.html` files while preserving folder landing pages as `index.html` under folder directories.

## Conclusion

Implemented unified runtime file URLs such as `/README.md` and `/Folder/B.md`, plus directory pages such as `/Folder/`.

Removed route-level permalink and alias overrides from page serving. Notes still keep aliases for link resolution and search matching, but the canonical page URL is now always the vault-relative file path with extension.

Updated the scanner, indexer, renderer, SEO helpers, web routes, Django views, and static builder so system-generated file labels use the filename with extension. Note body content remains user-authored and is not rewritten.

Added directory landing pages backed by the nav tree for the standalone app, Django integration, and static export. Directory pages render direct child folders and files as cards.

Updated the left navigation HTML, frontend behavior, and styles so folder titles navigate, the right-side arrow toggles expansion, and active/ancestor folders get a subtle color state.

Static export now writes note pages like `README.md.html` and text pages like `tools/example.py.html`, rewrites generated page links/search/graph URLs to those static targets, and keeps directory pages at paths like `Folder/index.html`.

## Changed Files

- `src/vaultpub/core/paths.py`
- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/index/indexer.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/core/render/seo.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/django_app/templates/vaultpub/page.html`
- `src/vaultpub/django_app/templates/vaultpub/partials/nav.html`
- `frontend/src/sidebar.ts`
- `frontend/src/nav-highlight.ts`
- `frontend/src/styles/base.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/unit/test_paths.py`
- `tests/unit/test_renderer.py`
- `tests/unit/test_seo.py`
- `tests/unit/test_indexer.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_paths.py tests/unit/test_renderer.py tests/unit/test_seo.py tests/unit/test_indexer.py tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `PATH=/data/p/bin:$PATH npm run build`

## Manual Verification

- Verified through automated integration tests that runtime note pages use file-extension URLs, directory pages render, and old extensionless routes return 404.
- Verified through automated static-builder tests that file pages emit `.html` targets and folder landing pages emit `index.html` under folder directories.
- Did not run an additional browser-only manual check beyond the passing test suite and frontend bundle build in this turn.
