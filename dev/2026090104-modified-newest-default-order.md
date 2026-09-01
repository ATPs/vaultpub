# Feature: modified-newest default folder order

## Goal

Default folder navigation to modification time, newest first, while preserving a folder's explicit `__order__.json` order when present.

## Conclusion

Fresh visitors now use Modified newest. Each folder with a non-empty `__order__.json` keeps its predefined order; folders without one use modification time. Stored visitor sort choices and starred-item precedence remain unchanged.

## Changed Files

- `frontend/src/sidebar.ts`
- `src/vaultpub/core/models.py`
- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `tests/unit/test_scanner.py`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`
- `dev/2026090104-modified-newest-default-order.md`

## Tests

- `npm run build` in `frontend/`
- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_scanner.py tests/unit/test_renderer.py tests/integration/test_web_app.py tests/django/test_django_app.py -q` (`79 passed`)

## Manual Verification

- Not performed.
