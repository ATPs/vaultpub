# Feature: clickable-breadcrumbs

## Goal

Make every breadcrumb segment clickable after the URL model change where:
- directories have public URLs
- files keep their extensions in public URLs

Verify this across standalone serve, static build, and Django mount-prefix rendering.

## Conclusion

Updated the shared breadcrumb renderer to generate links for every segment, including intermediate directories and the current file/directory entry.

The implementation now builds breadcrumb URLs from the same public URL model used elsewhere, with optional URL transforms for Django prefixes and static `.html` output.

Adjusted breadcrumb flex behavior so long linked segments can still shrink cleanly in the top bar.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/web/routes.py`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `PATH=/data/p/bin:$PATH /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `npm run build`

## Manual Verification

- Restarted preview tmux session `vaultpub-topbar-v1` on `http://10.110.120.2:8010/` without touching the user’s `8008` instance.
- Confirmed a real code page at `/tools/preprocessing/utils/prep_config.py` renders breadcrumb links for `Home`, `tools/`, `preprocessing/`, `utils/`, and `prep_config.py`.
