# Feature: directory list layout

## Goal

Use a default single-column card list for directory landing pages, visually distinguish folders from files, and show a wrapped two-line preview for file entries.

## Conclusion

Updated directory-page rendering to a single-column list where each item is still a card. Folder entries keep a distinct folder treatment, while file entries render filename-only titles plus a wrapped two-line preview built from the first two non-empty text lines.

Added focused test coverage for standalone web, Django, static export, and template rendering.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `frontend/src/styles/base.css`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`
- `tests/integration/test_static_builder.py`

## Tests

- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py::test_directory_page tests/django/test_django_app.py::test_django_directory_page tests/integration/test_static_builder.py::test_build_static_site`

## Manual Verification

- Rebuild frontend assets and verify the directory landing page renders a single-column card list with wrapped two-line file previews.
