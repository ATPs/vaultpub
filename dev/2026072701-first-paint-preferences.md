# Feature: first-paint preferences

## Goal

Restore the saved theme and top-folder navigation preference before the first browser paint so page navigation does not flash from light to dark or briefly show folders in the sidebar.

## Conclusion

Added a small synchronous bootstrap asset that applies the stored or system-resolved theme before CSS loads. When top-folder navigation is preferred, it temporarily hides the unresolved navigation regions and reveals them atomically after the existing frontend selects the final layout, with a safe fallback when initialization cannot enable the feature.

The asset is kept in both the Vite public source and the packaged static directory, so the editable install works immediately and future frontend builds retain it without changing the existing application bundle or localStorage formats.

## Changed Files

- `frontend/public/boot.js`
- `src/vaultpub/django_app/static/vaultpub/boot.js`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/core/export/static_builder.py`
- `tests/django/test_django_app.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `README.md`

## Tests

- `node --check frontend/public/boot.js`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/django/test_django_app.py tests/integration/test_web_app.py tests/integration/test_static_builder.py` — 45 passed.
- `/data/p/anaconda3/envs/django/bin/python -m pytest` — 176 passed.

## Manual Verification

- Used headless Chromium with a temporary page loading the packaged `boot.js` before `app.css`.
- Confirmed a dark system preference resolves to `theme-dark` before main initialization, an explicit Nord preference resolves to `theme-nord`, and an explicit Light preference remains light.
- Confirmed `topFolders: true` hides the unresolved file tree before initialization and reveals it after the top navigation becomes active; `topFolders: false` leaves the ordinary sidebar visible.
- No npm, pip, or conda package installation was run.
