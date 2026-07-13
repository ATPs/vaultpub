# Feature: JSON navigation control files

## Goal

Allow vault folders to define predefined ordering, pinned navigation entries, and folder presentation metadata without publishing those configuration files.

## Conclusion

Added reserved JSON-only dunder control files: `__order__.json`, `__star__.json`, and `__category__.json`. The server renders their predefined order, while the sidebar lets visitors persistently switch among name, creation-date, modification-date, and predefined sorting. Starred entries remain first in every sort mode.

## Changed Files

- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/security.py`
- `src/vaultpub/core/models.py`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/sidebar.ts`
- `frontend/src/styles/base.css`
- `src/vaultpub/core/realtime/watcher.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `README.md`
- unit tests and bundled static assets

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_scanner.py tests/unit/test_renderer.py tests/unit/test_security.py tests/unit/test_realtime_watcher.py -q`
- `npm run build` in `frontend/`

## Manual Verification

- Build a vault with all three controls, choose each navigation sort mode, and confirm starred entries remain first while directory pages and top-folder tabs follow the selected order.
