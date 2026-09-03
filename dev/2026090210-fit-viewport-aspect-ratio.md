# Feature: Fit viewport aspect-ratio alignment

## Goal

Make Fit viewport paginate against the selected Reveal slide canvas instead of the browser viewport.

## Conclusion

Fit pagination now uses Reveal's computed logical slide width and height after the current aspect setting is applied. A 21:9 canvas therefore has its own shorter Fit capacity, while Fit available space continues to use the browser dimensions through Reveal's existing configuration.

## Changed Files

- `frontend/src/slides.ts`
- `README.md`

## Tests

- `cd frontend && npm run build`
- Focused slide renderer, ASGI, and Django tests
- `git diff --check`

## Manual Verification

- Verify Fit viewport pagination with Fit available space, 21:9, 16:9, 4:3, and a custom ratio.
