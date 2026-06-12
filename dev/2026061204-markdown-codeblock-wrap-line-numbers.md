# Feature: markdown code block wrap and line numbers

## Goal

Make Markdown fenced code blocks wrap by default and display line numbers, without changing the backend Markdown rendering structure. Verify the behavior is present in packaged frontend assets and applies to rendered note pages.

## Conclusion

Implemented line-number decoration in the frontend after syntax highlighting, and changed default code block styling to wrap instead of forcing horizontal scroll. The enhancement applies to rendered `pre > code` blocks, including Markdown fenced code blocks and text-page code blocks, while keeping the backend HTML unchanged.

## Changed Files

- frontend/src/code-highlight.ts
- frontend/src/styles/base.css
- frontend/src/styles/highlight.css
- frontend/src/styles/layout.css
- src/vaultpub/django_app/static/vaultpub/app.css
- src/vaultpub/django_app/static/vaultpub/app.js
- tests/integration/test_web_app.py

## Tests

- `cd frontend && npm run build`
- `source /data/p/anaconda3/bin/activate base >/dev/null 2>&1 || true; export PATH=/data/p/bin:$PATH; /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py`

## Manual Verification

- Open a note containing a fenced Markdown code block and confirm long lines wrap by default.
- Confirm the same code block shows a left-side line number column.
- Refresh the page and confirm the packaged frontend assets still deliver the behavior through `/static/vaultpub/app.css` and `/static/vaultpub/app.js`.
