# Feature: responsive right sidebar drawer

## Goal

Make the page sidebar useful at every viewport width: keep it inline on wide screens and provide an accessible overlay drawer from a visible Page button on medium and phone screens.

## Conclusion

The right sidebar now uses a transient responsive drawer at 1180px and below instead of disappearing at medium widths or moving below the article on phones. Desktop collapse preferences remain separate from responsive drawer state.

## Changed Files

- `frontend/src/sidebar.ts`
- `frontend/src/mobile.ts`
- `frontend/src/styles/layout.css`
- `README.md`

## Tests

- `npm run build` completed successfully.
- `PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/django/test_django_app.py tests/integration/test_static_builder.py` passed (75 tests).

## Manual Verification

- Headless Chromium checks passed at 1440px, 1024px, 768px, and 390px.
- Verified desktop collapse persistence, responsive drawer state isolation, Escape/backdrop/contents-link closing, resize restoration, and no horizontal overflow.
