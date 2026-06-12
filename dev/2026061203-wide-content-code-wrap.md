# Feature: wide content and code wrap controls

## Goal

Add a top-bar toggle to switch page content between fixed reading width and full available width, and add code wrap controls for attachment code blocks with wrap enabled by default. Verify that the controls work for normal pages, standalone text pages, and embedded text attachments in both dynamic and static output.

## Conclusion

Implemented a global `Wide` toggle in the top bar with persisted state, changed code wrap to default on unless a prior stored preference exists, and added a small `Wrap` button to embedded text attachment code blocks. The wrap state is shared across standalone text pages and embedded text attachments. The sanitizer was updated to preserve the embedded button attributes so the frontend can bind to them.

## Changed Files

- frontend/src/topbar-context.ts
- frontend/src/styles/layout.css
- src/vaultpub/core/render/renderer.py
- src/vaultpub/core/render/sanitize.py
- src/vaultpub/core/render/templates.py
- src/vaultpub/django_app/templates/vaultpub/base.html
- src/vaultpub/django_app/static/vaultpub/app.css
- src/vaultpub/django_app/static/vaultpub/app.js
- tests/unit/test_renderer.py
- tests/django/test_django_app.py
- tests/integration/test_static_builder.py
- tests/integration/test_web_app.py

## Tests

- `cd frontend && npm run build`
- `source /data/p/anaconda3/bin/activate base >/dev/null 2>&1 || true; export PATH=/data/p/bin:$PATH; /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/django/test_django_app.py tests/integration/test_static_builder.py tests/integration/test_web_app.py`

## Manual Verification

- Open a note page and toggle `Wide`; confirm the content area expands to the available space and the preference persists across navigation.
- Open a note with an embedded text attachment and confirm the embedded code block shows a small `Wrap` button and wraps by default.
- Open a standalone text page and confirm the top-bar `Wrap` button starts active and stays in sync with embedded attachment code blocks.
