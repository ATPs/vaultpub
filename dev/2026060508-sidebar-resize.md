# Feature: sidebar resize

## Goal

Allow users to resize the left and right sidebars directly on the page with the mouse, while keeping existing collapse, peek, and responsive sidebar behavior intact.

## Conclusion

Added draggable resize handles to both desktop sidebars. Widths are stored in the existing sidebar local state and restored on reload. Left and right widths now use separate CSS variables so drag resize and collapsed off-canvas positioning stay in sync. Mobile and narrow responsive layouts keep their existing fixed behavior and hide the drag handles.

## Changed Files

- `frontend/src/sidebar.ts`
- `frontend/src/styles/base.css`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`

## Tests

- `cd frontend && npm run build`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`

## Manual Verification

- On desktop, move the mouse to the inner edge of the left sidebar and drag to resize it.
- On desktop, move the mouse to the inner edge of the right sidebar and drag to resize it.
- Reload the page and confirm both sidebar widths are restored.
- Collapse and reopen each sidebar and confirm its stored width is preserved.
- Reduce the viewport to mobile width and confirm resize handles are hidden and the mobile drawer behavior still works.
