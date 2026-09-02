# Feature: Slide View interaction and Fit repair

## Goal

Repair presenter-panel dismissal, centered glass dock behavior, compact Settings, and Fit Viewport segmentation without changing normal pages.

## Conclusion

Presenter panels now use explicit state rather than a dock pointer-leave timer. The dock is centered, faint after activity, and clear on hover, focus, or while a panel is open. Fit no longer pre-splits at H2 headings and measures content in a non-degenerate hidden surface before applying per-slide enlargement.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `src/vaultpub/core/render/slides.py`
- Slide renderer tests and documentation

## Tests

- `npm run build`
- Focused slide renderer, ASGI, and Django tests: 70 passed
- Full Python suite: 212 passed
- `git diff --check`

## Manual Verification

- Chromium rendered the fixture at `1440x900` and `390x844`; the mobile dock was visible without clipping and the desktop dock entered its intended idle state.
- The live server on port 9000 is not restarted.
