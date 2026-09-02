# Feature: slide presenter controls

## Goal

Make live Slide View feel like a presentation application: persistent viewer settings, explicit split control, navigation, fullscreen, live presenter tools, and touch support without changing source Markdown.

## Conclusion

Added validated `slide.split` and `slide.codeWrap` author defaults, URL/cookie split precedence, a compact fading presenter dock, settings, searchable navigation, fullscreen, timer/blackout, laser, magnifier, and temporary per-slide drawing. The same rendering rules apply to Django and the standalone server. Static export remains article-only.

## Changed Files

- `src/vaultpub/core/render/slides.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `frontend/public/slides-boot.js`
- `README.md`
- slide unit and route tests

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest -q tests/unit/test_slides.py tests/integration/test_web_app.py tests/django/test_django_app.py`
- `cd frontend && npm run build`

## Manual Verification

- Started the standalone server for `tests/fixtures/vault_slides_demo` and inspected `/_slides/auto-slides.md` in Chromium headless at a 1440x900 viewport.
- Confirmed the deck renders with the dock clear of slide content, settings metadata and bootstrap assets load, and the live DOM contains the dock, settings, picker, laser, and drawing overlays.
- Confirmed settings open with code wrapping enabled, pen activates its canvas/tools, laser replaces pen, magnifier activates and `Escape` exits it, the title picker lists three slides, and blackout toggles.
- Confirmed the dock enters its idle-faded state after 2.5 seconds and reappears on pointer movement.
- Fullscreen browser permission and physical touch/stylus drawing remain environment-dependent manual checks.
