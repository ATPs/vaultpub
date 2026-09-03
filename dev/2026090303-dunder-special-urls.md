# Feature: Dunder special URLs

## Goal

Move VaultPub-owned special endpoints to Python-style dunder URL names so ordinary vault folders can use the former route names without collisions.

## Conclusion

Standalone and Django routes now use `__slides__`, `__slides-folder__`, `__slides-vault__`, `__settings__`, `__api__`, and `__assets__`. Old special URLs are not registered or redirected. Exact new dunder roots are excluded from vault publication, while nested dunder names remain available. Static SEO/data filenames and `/static/vaultpub` remain unchanged.

## Changed Files

- Shared URL constants, attachment paths, scanner/security, realtime filtering, and renderer/static-builder URL handling.
- Standalone and Django routes/views/templates, frontend API callers, README, and regression tests.
- Rebuilt frontend bundle.

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest -q` — 226 passed.
- `/data/p/anaconda3/envs/django/bin/python -m compileall -q src tests` — passed.
- `git diff --check` — passed.
- `npm run build` from `frontend/` — passed.

## Manual Verification

- No browser verification performed.
- Frontend build ran in tmux session `vaultpub_dunder_urls_build2` and completed successfully.
