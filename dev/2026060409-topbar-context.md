# Feature: topbar-context

## Goal

Use the empty middle area of the top bar for page-aware context:
- note pages show breadcrumb + current heading
- force-included text/code pages show breadcrumb + lightweight code tools

Verify in all render paths that matter for `vaultpub`: standalone serve, static build, and Django template rendering.

## Conclusion

Implemented a shared top bar context block and wired it into the standalone web app, static export, and Django integration.

For note pages, the top bar now renders a breadcrumb trail plus a client-updated current-heading pill.

For text/code pages, the top bar now renders a breadcrumb trail plus language/size metadata, a copy-path button, and a wrap toggle backed by localStorage.

The frontend bundle was rebuilt so the packaged static assets match the new source.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `frontend/src/app.ts`
- `frontend/src/theme.ts`
- `frontend/src/topbar-context.ts`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `PATH=/data/p/bin:$PATH /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `npm run build`

## Manual Verification

- Started a standalone server in tmux session `vaultpub-topbar-v1` on `http://10.110.120.2:8010/` for vault `/data2/pub/proteome/web/protinsight/comet/`.
- Confirmed `/` returns `200` and includes `topbar-context topbar-context-note`, breadcrumb `Home / README.md`, and a current-heading placeholder.
- Confirmed a real `.py` page returns `topbar-context topbar-context-code`, breadcrumb segments, `Python · size`, `Copy path`, and `Wrap`.
- Attempted a browser-level Playwright smoke test, but local Playwright is missing the Chrome distribution and exits with `Run "npx playwright install chrome"`.
