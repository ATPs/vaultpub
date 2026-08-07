# Feature: Mobile share initial scroll

## Goal

Prevent shared note pages from automatically scrolling to the bottom when opened on a mobile viewport.

## Conclusion

Replaced document-affecting `scrollIntoView()` calls in navigation highlighting with bounded scrolling of the corresponding sidebar. The mobile table of contents has no independent scroll range, so its initial active link no longer moves the document.

## Changed Files

- `frontend/src/nav-highlight.ts`
- `pyproject.toml`
- `src/vaultpub/__init__.py`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`
- `dev/2026080702-mobile-share-initial-scroll.md`

## Tests

- `npm run build`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py`

## Manual Verification

- Opened the reported shared page in headless Chromium with a mobile viewport and confirmed the initial document scroll position remains at the top.
