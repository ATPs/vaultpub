# Feature: Single table-of-contents heading

## Goal

Show only one "Contents" heading in the right sidebar table of contents on Django-rendered note pages.

## Conclusion

Removed the redundant table-of-contents wrapper from the Django partial. The renderer-provided navigation now supplies the sole "Contents" heading and TOC container.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/partials/toc.html`
- `tests/django/test_django_app.py`
- `dev/2026071306-single-toc-heading.md`

## Tests

- Added a regression assertion that a Django note page contains exactly one `<h3>Contents</h3>` heading.

## Manual Verification

- Confirm the right sidebar on a note with headings displays one "Contents" label followed by its heading links.
