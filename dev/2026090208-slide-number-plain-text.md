# Feature: Remove Slide View number

## Goal

Remove the redundant floating Slide View number because the presenter dock already reports slide position.

## Conclusion

Reveal slide numbering is disabled during initialization and later configuration updates. The Settings toggle and documented frontmatter example were removed; the dock counter remains the single position indicator.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `README.md`

## Tests

- `cd frontend && npm run build`
- `git diff --check`

## Manual Verification

- Verify that no floating number is rendered in standalone, folder, or vault Slide View decks.
