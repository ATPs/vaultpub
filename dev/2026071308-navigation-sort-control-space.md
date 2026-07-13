# Feature: navigation sort control space

## Goal

Make the navigation ordering control readable without wasting sidebar-header space on a redundant label.

## Conclusion

Removed the left-sidebar `Navigation` heading and made the sort selector flex into the released space while retaining the tree and sidebar controls.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/styles/layout.css`
- `frontend/src/styles/base.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`

## Tests

- `npm run build` in `frontend/`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py -q`

## Manual Verification

- Confirm the left sidebar shows a full-width readable sort selector alongside the navigation controls.
