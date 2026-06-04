# Feature: scroll blank fix

## Goal

Fix the page going blank or leaving sidebar gaps when scrolling on served code pages, especially `/tools/preprocessing/utils/prep_alpha2rescore_io_helper.py`.

Verify that hiding the top bar does not apply a page-level transform to `<body>`.
Verify that sidebars fill the viewport and show the replacement logo/search region when the top bar is hidden.

## Conclusion

The recent top-bar auto-hide update added `top-bar-hidden` to `<body>` for sidebar layout state, but the CSS rule `.top-bar-hidden { transform: translateY(-100%); }` also matched `<body>`. This moved the entire page out of the viewport and produced a blank page.

Scoped the transform rule to `.top-bar.top-bar-hidden` so only the top bar is translated while `body.top-bar-hidden` remains available for sidebar layout rules.

Follow-up verification showed that when the sidebars moved to `top: 0`, their height still remained `calc(100vh - var(--topbar-height))`, which left a bottom gap. The standalone web template also lacked the `.sidebar-top` replacement controls that already existed in the Django template, so the navigation appeared to jump upward instead of showing logo/search in the vacated top-bar region.

Updated standalone rendering to include the same left logo/title and right search replacement regions, and made hidden-topbar sidebars use `height: 100vh`.

## Changed Files

- `frontend/src/styles/layout.css`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `dev/2026060408-scroll-blank-fix.md`

## Tests

- `PATH=/data/p/bin:$PATH npm run build`
- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit tests/integration`
- `PATH=/data/p/bin:$PATH PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/integration/test_static_builder.py`

## Manual Verification

- Started `vaultpub serve --vault /data2/pub/proteome/web/protinsight/comet/ --host 0.0.0.0 --port 8008 --force-include-regex '.*\.py$'` from current source in tmux.
- Confirmed served CSS contains `.top-bar.top-bar-hidden{transform:translateY(-100%)}`.
- Used Chromium to open `http://127.0.0.1:8008/tools/preprocessing/utils/prep_alpha2rescore_io_helper.py`, scroll down, then scroll up.
- Confirmed `body` keeps `transform: none`; only the top bar translates while hidden, and source content remains visible.
- Confirmed hidden-topbar sidebars are `top: 0`, `height: 100vh`, and `bottom` equals the viewport bottom.
- Confirmed standalone pages now include `.sidebar-top`, with `vaultpub` shown in the left sidebar and `Search (Ctrl+K)` shown in the right sidebar while the top bar is hidden.
