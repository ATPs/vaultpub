# Feature: Hide Navigation Root

## Goal

Make the left navigation show vault contents directly instead of starting with a `/` root directory node.

## Conclusion

Updated the navigation tree renderer to unwrap the root `NavNode(label="/")` and render only its children at the top level. Folder nodes below the root keep their existing labels and `data-nav-key` values, so persisted folder collapse state remains compatible.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `tests/unit/test_renderer.py`

## Tests

- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py tests/django/test_django_app.py`
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest`
- `/data/p/anaconda3/envs/django/bin/python -m ruff check src/vaultpub/core/render/templates.py tests/unit/test_renderer.py`
- `git diff --check`

## Manual Verification

- Added a renderer test confirming `<summary>/</summary>` is absent while root-level vault files and folders still render.
