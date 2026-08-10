# Feature: readable frontend bundle

## Goal

Generate frontend JavaScript with readable line breaks so packaged bundle changes can be inspected in version control.

## Conclusion

Kept Vite's normal compression for CSS and dynamic chunks, then formatted only the generated `app.js` entry bundle after output generation. This keeps the production asset payload compact while making the tracked entry bundle easier to inspect.

## Changed Files

- `frontend/vite.config.ts`
- Generated `src/vaultpub/django_app/static/vaultpub/app.js` (not tracked by Git)
- `dev/2026081002-readable-frontend-bundle.md`

## Tests

- Ran `npm run build` in `frontend/`.

## Manual Verification

- Confirmed the generated `app.js` contains formatted multi-line code.
- Confirmed the generated entry bundle still imports its dynamic frontend chunks.
