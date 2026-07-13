# Feature: top folder navigation

## Goal

Add a OneNote-style top-bar folder navigator that can replace the left tree's top-level folders without increasing the top-bar height.

## Conclusion

Added a persisted folder-layout toggle. When enabled, root files and each top-level folder are selectable from a one-line top-bar tab strip, while the left navigator shows the selected section's contents. Excess tabs move into an accessible overflow menu.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/sidebar.ts`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `npm run build` in `frontend/`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`

## Manual Verification

- In headless Chromium, toggled the feature on a vault with a root file and `Folder/`; confirmed `Root` and `Folder` tabs render, selecting `Folder` leaves the current page URL unchanged and shows `B.md` in the left navigator, and the top-bar height stays 52px.
- Reloaded after enabling the feature and confirmed the persisted mode restores the active top-folder navigation.
