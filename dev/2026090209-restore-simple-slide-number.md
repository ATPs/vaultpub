# Feature: Restore simple Slide View number

## Goal

Restore the optional page number as plain visible text after removing the redundant badge treatment.

## Conclusion

Regular Slide View decks again honor their saved or frontmatter slide-number setting. The number is positioned from Reveal's stable slide stage and remains plain theme-coloured text without a border, background, padding, shadow, or blur. Single-page Slide View continues to hide it.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `README.md`

## Tests

- `cd frontend && npm run build`
- `git diff --check`

## Manual Verification

- Verify regular slide decks show the number at the lower-right slide edge and Single does not.
