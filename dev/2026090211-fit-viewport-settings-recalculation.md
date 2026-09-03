# Feature: Fit viewport settings recalculation

## Goal

Rebuild Fit viewport pages after committing an aspect-ratio change, including the Fit available space choice.

## Conclusion

Select settings now use their committed `change` event. Fit pagination waits for Reveal's layout frame to settle before rebuilding pages, so aspect changes use the final canvas dimensions.

## Changed Files

- `frontend/src/slides.ts`
- `README.md`

## Tests

- `cd frontend && npm run build` (passed)
- `/data/p/anaconda3/envs/django/bin/python -m pytest -q tests/unit/test_slides.py tests/integration/test_web_app.py tests/django/test_django_app.py` (73 passed)
- `git diff --check` (passed)

## Manual Verification

- Not run: browser automation is unavailable in this environment.
- Manually switch from a fixed ratio to Fit available space while using Fit viewport and confirm page content is regenerated.
