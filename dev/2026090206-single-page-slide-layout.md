# Feature: single-page Slide View layout

## Goal

Make the existing `?split=single` Slide View fill the viewport cleanly for embedding-style reading, with the scrollbar at the page edge and no Reveal corner slide number.

## Conclusion

Single-note `split=single` now uses a zero-margin Reveal viewport, keeps the floating presenter dock unchanged, hides Reveal's bottom-right slide number, and uses a thin subdued scrollbar that becomes clearer on hover. Normal and multi-note slide decks retain their existing layout.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/templates/vaultpub/slides.html`
- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`
- `README.md`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest -q tests/unit/test_slides.py tests/integration/test_web_app.py tests/django/test_django_app.py` — 73 passed.
- `cd frontend && npm run build` — passed.
- `git diff --check` — passed.

## Manual Verification

- Served `tests/fixtures/vault_slides_demo/long-single-slide.md` locally and confirmed the single layout marker is present only for `?split=single`, not `?split=sections`.
- Chromium headless cannot start in this environment: it exits before opening `about:blank` with Crashpad I/O errors. Visual desktop/mobile geometry and interactive dock verification remain pending in a working browser.
