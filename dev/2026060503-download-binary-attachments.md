# Feature: download-binary-attachments

## Goal

Publish download-style binary attachments such as `.pin.gz` by default and avoid rendering them as broken images when referenced from Markdown image syntax.

Verification targets:
- `![filename](../../3A0S.pin.gz)` renders as a clickable link to `/assets/tools/3A0S.pin.gz`
- common compressed/binary download files are scanned as attachments by default
- standalone and Django attachment responses include `Content-Disposition: attachment`
- static build keeps the generated download link and copies the file into `assets/`

## Conclusion

Added a shared attachment helper module for default downloadable attachment types, MIME detection, image-vs-download classification, and `Content-Disposition` generation.

The renderer now:
- treats common compressed files as published attachments
- degrades Markdown and raw-HTML image tags that point at non-image local files into links
- adds `download="filename"` for download-only attachments such as `.gz`

The runtime attachment views now return `Content-Disposition` for download-only files, and config loading now accepts `allowed_attachment_types` from YAML and Django settings.

## Changed Files

- `src/vaultpub/core/attachments.py`
- `src/vaultpub/core/config.py`
- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/core/render/sanitize.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/django_app/conf.py`
- `README.md`
- `tests/fixtures/vault_local_resources/subdir/README.md`
- `tests/fixtures/vault_local_resources/subdir/archive.pin.gz`
- `tests/unit/test_config.py`
- `tests/unit/test_scanner.py`
- `tests/unit/test_renderer.py`
- `tests/unit/test_sanitize.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest`

## Manual Verification

- Confirmed the real vault example now resolves to `/assets/tools/3A0S.pin.gz` instead of staying a broken relative image
- Confirmed download-only attachments return `Content-Disposition: attachment; filename="..."` in both ASGI and Django modes
