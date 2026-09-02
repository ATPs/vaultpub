# Feature: UI regression repair

## Goal

Restore the normal-view appearance from the known-good `d5f711c` baseline while retaining the newer Slide View behavior.

## Conclusion

The regression came from Vite extracting CSS shared by `app.ts` and `slides.ts` into `slides.css`. Normal pages load only `app.css`, so they lost the reset, reading-theme, file-tree, Markdown, callout, and syntax-highlight styles.

Created a deterministic `common.css` bundle for those shared styles and load it before `app.css` or `slides.css` in ASGI, Django, and static HTML. This restores the normal view to the `d5f711c` styling boundary while preserving Slide View controls and themes. Build assertions and rendered-page tests now require the shared bundle and stylesheet ordering.

## Changed Files

- `frontend/src/styles/common.css`
- `frontend/vite.config.ts`
- `frontend/scripts/build.mjs`
- `frontend/src/styles/slides.css`
- `frontend/src/styles/themes.css`
- `frontend/src/app.ts`
- `frontend/src/icons.ts`
- `frontend/src/slides.ts`
- `frontend/package.json`
- `frontend/package-lock.json`
- ASGI, Django, and static HTML templates
- ASGI, Django, and static builder regression tests

## Tests

- Pending final build and full test-suite verification.

## Manual Verification

- Pending final browser verification. The authenticated production page on port 9000 is not restarted or modified by this repair.
