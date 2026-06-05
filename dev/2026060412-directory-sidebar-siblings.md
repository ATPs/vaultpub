# Feature: directory sidebar siblings

## Goal

When viewing a directory page, use the right sidebar as directory navigation by showing links to files that live alongside the current folder, and change the sidebar title accordingly.

## Conclusion

Added a dedicated directory sidebar block that lists sibling files from the current folder's parent directory. Directory pages now label the right sidebar as `Directory` instead of `Page`.

Applied the behavior across standalone web, Django, and static export, and added focused tests for the new sidebar content.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `frontend/src/styles/base.css`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`
- `tests/integration/test_static_builder.py`

## Tests

- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py::test_directory_page tests/django/test_django_app.py::test_django_directory_page tests/integration/test_static_builder.py::test_build_static_site`

## Manual Verification

- Open a directory page and confirm the right sidebar title changes to `Directory` and the file links point to sibling files in the parent directory.
