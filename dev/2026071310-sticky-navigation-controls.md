# Feature: sticky navigation controls

## Goal

Keep the left navigation controls available while scrolling a long navigation tree.

## Conclusion

Wrapped the left sidebar's top area and controls in a sticky, opaque container. The site label (when the top bar is hidden), ordering selector, expand/collapse controls, layout toggle, and sidebar toggle now remain visible during navigation scrolling.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`

## Tests

- `npm run build` in `frontend/`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py -q`

## Manual Verification

- Scroll a long left navigation tree and confirm the control row remains pinned at the top of the sidebar.
