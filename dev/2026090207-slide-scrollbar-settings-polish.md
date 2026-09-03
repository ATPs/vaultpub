# Feature: Slide View scrollbar and settings polish

## Goal

Use the established subtle scrollbar treatment across Slide View, place scaled-deck scrolling at the browser edge, float the optional slide number inside each slide, and compact the Settings popup.

## Conclusion

Single-page Slide View keeps its native edge scrollbar. Other slide layouts now use a synchronized, draggable and keyboard-accessible edge rail while leaving Reveal's scaled slide geometry unchanged. The Reveal number is positioned from the active slide bounds, keeping it inside the lower-right corner. Settings no longer stretches the Theme group into unused space; it groups theme, display, split, and toggle controls responsively. Split choices expose explanatory hover and focus messages.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `README.md`
- Generated Slide View frontend assets

## Tests

- `cd frontend && npm run build`
- Focused Slide View renderer, ASGI, and Django tests
- `git diff --check`

## Manual Verification

- Browser verification is pending because Chromium headless exits with Crashpad I/O errors before producing a screenshot in this environment.
