# Feature: sidebar nav controls

## Goal

Add top-level controls in the left navigation to expand or collapse every folder, and add dotted guide lines so expanded folder contents are easier to read by depth.

## Conclusion

Added `Expand all` and `Collapse all` buttons to the left sidebar header in both render paths. Hooked them into the existing nav tree `localStorage` state so bulk changes persist like individual folder toggles. Added dotted guide lines for nested folder children in the file tree.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/sidebar.ts`
- `frontend/src/styles/base.css`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `cd frontend && npm run build`

## Manual Verification

- Confirm the left sidebar shows `Expand all` and `Collapse all` above the tree.
- Click `Expand all` and verify every folder opens.
- Click `Collapse all` and verify every folder closes.
- Reload after toggling and confirm the tree keeps the stored bulk state, with current-page ancestors still reopening from existing nav highlighting behavior.
- Expand nested folders and confirm dotted guide lines show shared depth clearly.
