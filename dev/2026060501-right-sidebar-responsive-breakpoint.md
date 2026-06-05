# Feature: right sidebar responsive breakpoint

## Goal

On narrower desktop/tablet widths, hide the right sidebar before switching to the existing mobile behavior where both side navigations are hidden.

## Conclusion

Added an intermediate responsive breakpoint so the right sidebar is hidden between desktop and mobile widths, while the left navigation remains visible. The existing mobile breakpoint behavior remains unchanged.

Added a lightweight asset assertion to ensure the packaged CSS includes the new breakpoint.

## Changed Files

- `frontend/src/styles/layout.css`
- `tests/integration/test_web_app.py`

## Tests

- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py::test_frontend_static_assets`
- `PATH=/data/p/bin:$PATH npm run build`

## Manual Verification

- Verify that around tablet-width desktop sizes the right sidebar disappears while the left navigation remains visible, and that below the mobile breakpoint the existing hide-both behavior still applies.
