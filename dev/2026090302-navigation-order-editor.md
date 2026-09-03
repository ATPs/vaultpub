# Feature: navigation order editor

## Goal

Provide a Settings entry and live page for arranging published subfolders and files without moving any vault content.

## Conclusion

Added a live-only Custom order page for standalone and Django sites. It writes or removes only per-folder `__order__.json` files, keeps starred entries fixed, separates folder/file ordering, preserves non-visible legacy entries, and refreshes the live navigation immediately.

## Changed Files

- `src/vaultpub/core/navigation_order.py`
- `src/vaultpub/web/` and `src/vaultpub/django_app/`
- `frontend/src/order-editor.ts`
- `frontend/src/theme.ts` and `frontend/src/styles/layout.css`
- focused unit, standalone, Django, and static-export tests

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_navigation_order.py tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py -q`
- 63 passed
- `/data/p/anaconda3/envs/django/bin/python -m pytest -q`
- 220 passed
- `npm run build` in `frontend/`

## Manual Verification

- Standalone server smoke check passed for `/_settings/order` and `/api/settings/order`.
- Chromium could request the page but could not create a headless screenshot because its crash reporter failed with a container I/O error.
