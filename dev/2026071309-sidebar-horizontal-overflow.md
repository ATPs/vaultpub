# Feature: sidebar horizontal overflow

## Goal

Prevent the left navigator from displaying a horizontal scrollbar when nested folders or long labels exceed its width.

## Conclusion

The sidebar now clips horizontal overflow, and file-tree lists and folder summaries are constrained to their available width so labels continue wrapping in place.

## Changed Files

- `frontend/src/styles/layout.css`
- `frontend/src/styles/base.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`

## Tests

- `npm run build` in `frontend/`

## Manual Verification

- Open a deeply nested vault with long filenames and confirm labels wrap without a horizontal sidebar scrollbar.
