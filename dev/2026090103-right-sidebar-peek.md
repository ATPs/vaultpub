# Feature: right sidebar full-height peek

## Goal

Fix the collapsed right sidebar hover popup so its shadow and hover region use the full available viewport height, and prevent its floating reveal control from appearing offset from the sidebar control.

## Conclusion

The right sidebar now remains full-height while peeking, including when the top bar is hidden. Its floating reveal button aligns with the sidebar header inset, while the duplicate underlying hide button is hidden until the sidebar is opened. The left navigation retains its compact content-height peek behavior.

## Changed Files

- `frontend/src/styles/layout.css`
- `dev/2026090103-right-sidebar-peek.md`

## Tests

- `cd frontend && npm run build`
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/django/test_django_app.py tests/integration/test_static_builder.py` — 54 passed
- `git diff --check`

## Manual Verification

- Not run: the supplied live report URL redirects to the Django login page in this environment.
