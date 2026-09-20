# Feature: Markdown comments and task lists

## Goal

Hide standard HTML comments in rendered Markdown and display Markdown task
items as read-only checkboxes without weakening safe-mode raw HTML handling.

## Conclusion

VaultPub now removes well-formed `<!-- ... -->` comments from rendered output,
including the published response body. It preserves comment-like text in inline
and fenced code. Markdown task items render as disabled native checkboxes and
survive the HTML sanitization pass. The shared CSS removes duplicate list
markers and aligns each checkbox with its task text. Follow-on feature
`2026092002-local-task-checkboxes.md` makes those task inputs locally
interactive.

## Changed Files

- `src/vaultpub/core/parser/markdown.py`
- `src/vaultpub/core/render/sanitize.py`
- `frontend/src/styles/base.css`
- `src/vaultpub/django_app/static/vaultpub/common.css`
- Markdown, renderer, and sanitization unit tests

## Tests

- `python -m pytest -q tests/unit/test_markdown.py tests/unit/test_sanitize.py tests/unit/test_renderer.py` — 38 passed.
- `python -m ruff check src/vaultpub/core/parser/markdown.py src/vaultpub/core/render/sanitize.py tests/unit/test_markdown.py tests/unit/test_sanitize.py tests/unit/test_renderer.py` — passed.
- `npm run build` in `frontend/` — passed.
- `python -m pytest -q` — 266 passed.
- `git diff --check` — passed.

## Manual Verification

- Reloaded the supplied shared page. Its HTML contains four disabled
  `task-list-item-checkbox` inputs and no longer contains the teacher comment
  or literal `[ ]` task markers.
- Chromium loaded the shared page successfully. The headless run reported
  non-fatal GPU shared-image diagnostics while saving the screenshot.
