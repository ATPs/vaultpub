# Feature: static asset routing

## Goal

Serve the bundled frontend assets from `vaultpub serve` so requests for `/static/vaultpub/app.css` and `/static/vaultpub/app.js` return 200 instead of being handled by the page catch-all route.

Verify with the ASGI integration tests and a direct TestClient request for both asset URLs.

## Conclusion

Registered the Starlette static mount before the catch-all `/{path:path}` route. The catch-all now remains last, so note pages still resolve while bundled frontend assets are served by `StaticFiles`.

## Changed Files

- `src/vaultpub/web/app.py`
- `tests/integration/test_web_app.py`
- `dev/2026060401-static-asset-routing.md`

## Tests

- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py`

## Manual Verification

- Direct TestClient requests returned:
  - `/static/vaultpub/app.css` -> `200 text/css; charset=utf-8`
  - `/static/vaultpub/app.js` -> `200 application/javascript`
