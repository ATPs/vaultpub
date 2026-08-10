# Feature: readable frontend bundle

## Goal

Generate frontend JavaScript with readable line breaks so packaged bundle changes can be inspected in version control.

## Conclusion

Disabled Vite minification for the packaged frontend bundle. This produces formatted JavaScript and CSS while preserving the existing asset names and import structure. The trade-off is a larger uncompressed static payload; deployments can still apply HTTP compression.

## Changed Files

- `frontend/vite.config.ts`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `dev/2026081002-readable-frontend-bundle.md`

## Tests

- Ran `npm run build` in `frontend/`.

## Manual Verification

- Confirmed the generated `app.js` contains formatted multi-line code.
- Confirmed the generated entry bundle still imports its dynamic frontend chunks.
