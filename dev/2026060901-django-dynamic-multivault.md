# Feature: Django dynamic multi-vault helpers

## Goal

Allow a host Django project to render multiple VaultPub vaults dynamically from caller-provided `PublisherConfig` objects, including folder-scoped views for temporary shares.

## Conclusion

Added dynamic render helpers in `vaultpub.django_app.views`, made `PublisherConfig.include_folders` filter scanned notes/attachments/text pages, and changed Django attachment serving to stream files with `FileResponse`. Existing single-vault Django routes still use the default settings-based config.

## Changed Files

- `src/vaultpub/core/scanner.py`
- `src/vaultpub/django_app/views.py`
- `tests/unit/test_scanner.py`
- `tests/django/test_django_app.py`

## Tests

- Added scanner coverage for `include_folders`.
- Added Django adapter coverage for caller-supplied dynamic configs and streamed attachments.

## Manual Verification

- Intended host integration is `/database/vaultpub/` in `xcWebServer`; it calls the new dynamic helpers instead of static export.
