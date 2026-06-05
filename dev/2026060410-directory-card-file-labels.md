# Feature: directory card file labels

## Goal

Adjust directory landing page cards so file cards only show the filename, without rendering the relative path as secondary text.

## Conclusion

Updated directory-page rendering so only folder cards show secondary metadata. File cards now render just the filename title.

Added focused integration assertions for standalone web, Django, and static export directory pages to ensure file-card path metadata is absent.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`
- `tests/integration/test_static_builder.py`

## Tests

- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py::test_directory_page tests/django/test_django_app.py::test_django_directory_page tests/integration/test_static_builder.py::test_build_static_site`

## Manual Verification

- No separate browser-only manual verification in this turn.
