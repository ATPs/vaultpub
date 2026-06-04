# Feature: Frontend Build Release Flow

## Goal

Make Python package builds generate the frontend bundle automatically, keep Vite output out of normal Git tracking, and ensure `frontend/node_modules` is removed after frontend builds.

## Conclusion

Added a Hatch custom build hook that runs `npm run build` before wheel packaging. Reworked the frontend `build` script so it installs dependencies, runs the Vite/TypeScript bundle, and removes `frontend/node_modules` in a `finally` block. Added a lockfile so builds use `npm ci`, ignored generated frontend static output, and force-included the generated static directory into wheels.

## Changed Files

- `.gitignore`
- `README.md`
- `help/guide.md`
- `pyproject.toml`
- `hatch_build.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/scripts/build.mjs`

## Tests

- `npm install --package-lock-only --ignore-scripts`
- `npm run build`
- `/data/p/anaconda3/envs/django/bin/python -m pip wheel . --no-deps -w dist`
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest`
- `git diff --check`

## Manual Verification

- Confirmed `frontend/node_modules` is absent after `npm run build`.
- Confirmed the built wheel contains `vaultpub/django_app/static/vaultpub/app.css`, `app.js`, and 111 files under `vaultpub/django_app/static/vaultpub/assets/`.
