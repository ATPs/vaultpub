# Feature: Slide deck controls refinement

## Goal

Refine Slide View into a dock-owned presentation experience with reading themes, richer deck settings, fit-aware layout, and a vertically scrollable slide grid.

## Conclusion

Reveal controls and the standalone return link were removed in favour of dock controls. Settings now use explanatory choice cards, reading-theme swatches, a pointer/focus-aware popup, expanded text and ratio choices, and the new split policies. The deck also provides shortcut help, fullscreen, drawing tools, and an application-owned grid overlay.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `frontend/src/theme-data.ts`
- `frontend/src/theme.ts`
- `frontend/public/slides-boot.js`
- `src/vaultpub/core/render/slides.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/templates/vaultpub/slides.html`
- `README.md`
- slide renderer tests

## Tests

- `npm run build`
- focused slide renderer, ASGI, and Django tests

## Manual Verification

- Chromium loaded the built standalone deck at desktop size. The dock correctly fades while idle, and the generated DOM contains the dock, settings popup, and grid overlay. Interactive popup, touch, and fit-repagination assertions are covered by the frontend implementation and targeted test contracts; full device-emulation automation is not included in this repository.
