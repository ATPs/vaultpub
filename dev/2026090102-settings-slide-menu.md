# Feature: Settings menu and whole-vault Slide View

## Goal

Provide a persistent Settings menu for theme, layout, and Slide View actions, and add a live-only whole-vault Reveal deck at `/_slides-vault`.

## Conclusion

Replaced direct presentation links with Settings-menu actions backed by hidden page context data. The menu contains Wide content and bottom-positioned theme choices, while the existing sidebar Folders in top bar control remains unchanged. Added Django and ASGI whole-vault decks that follow canonical navigation order and return to the vault. Static output receives no slide URLs or slide actions.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/`
- `src/vaultpub/web/`
- `frontend/src/theme.ts`
- `frontend/src/sidebar.ts`
- `frontend/src/styles/layout.css`
- `tests/django/test_django_app.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `README.md`

## Tests

- `cd frontend && npm run build`
- `/data/p/anaconda3/envs/django/bin/python -m pytest` — 202 passed

## Manual Verification

- Not run; automated route, static-export, and frontend-build coverage passed.
