# Feature: Slide View windowed loading

## Goal

Ensure whole-vault and folder Slide View do not render every source note or activate every media resource in one browser response.

## Conclusion

Multi-note decks now send a lightweight note/fragment manifest and request one rendered note at a time. The browser retains at most the active note and its immediate neighbours, activates media only on the active note, and limits Fit processing and content thumbnails to that window. Multi-file printing is blocked because a complete export would violate the resource boundary. Single-note Slide View retains its original rendering and print behavior.

## Changed Files

- `src/vaultpub/core/render/slides.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `README.md`

## Tests

- Focused unit, ASGI, and Django slide tests.
- Frontend production build.

## Manual Verification

- Not completed: headless Chromium exited with Crashpad I/O errors (`exit 133`) before loading `about:blank`, so it could not verify hydration, layout, or screenshot output in this environment.
- Automated route tests confirm the multi-note print notice is emitted; browser print behavior remains a manual follow-up.
