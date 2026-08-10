# Feature: package frontend assets on build

## Goal

Keep generated frontend assets out of Git while retaining self-contained installable wheel packages.

## Conclusion

Removed the generated `app.js` and `app.css` files from Git tracking while retaining their existing ignore rules. The Hatch build hook builds the frontend before the wheel force-includes the generated files and assets; the hand-maintained `boot.js` remains part of the normal package collection. This avoids duplicate archive paths while keeping prebuilt wheels self-contained.

## Changed Files

- `src/vaultpub/django_app/static/vaultpub/app.js` (removed from Git tracking)
- `src/vaultpub/django_app/static/vaultpub/app.css` (removed from Git tracking)
- `pyproject.toml`
- `dev/2026081004-package-frontend-assets-on-build.md`

## Tests

- Build the v0.9.4 wheel from the repository.
- Inspect the wheel contents for the frontend static assets.

## Manual Verification

- Confirm generated assets remain present locally and are ignored by Git.
- Confirm `boot.js` remains tracked as a hand-maintained static file.
