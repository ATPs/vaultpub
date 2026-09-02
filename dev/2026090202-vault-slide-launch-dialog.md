# Feature: vault slide launch dialog

## Goal

Let users launch a multi-note Slide View for the whole vault or an eligible subfolder, with the same ordering rules as normal navigation and clear boundaries between source notes.

## Conclusion

Vault in Slide View now opens an accessible native dialog for scope and deck-only ordering. Django and ASGI pages provide only eligible scopes, folder routes remain compatible, and multi-note decks insert title/path divider slides before every Markdown source file. Existing presenter settings and controls continue to apply to all decks.

## Changed Files

- `frontend/src/slide-launch.ts`
- `frontend/src/theme.ts`
- `src/vaultpub/core/render/slides.py`
- `src/vaultpub/core/render/templates.py`
- Django and ASGI slide/page routes
- Slide, route, and static-export tests

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest -q tests/unit/test_slides.py tests/integration/test_web_app.py tests/django/test_django_app.py tests/integration/test_static_builder.py` — 75 passed.
- `cd frontend && npm run build` — generated the updated frontend bundles and cleaned `frontend/node_modules`.

## Manual Verification

- Not run in a browser. The dialog’s desktop/mobile layout, focus behavior, and presenter dock interaction remain manual checks.
