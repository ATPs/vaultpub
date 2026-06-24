# Feature: code line layout fix

## Goal

Fix Markdown fenced code blocks whose highlighted line-number layout can collapse and render code text one character per line. Verify the affected multi-line Python string is decorated as valid numbered code rows in a browser.

## Conclusion

Made `pre code` and highlighted `pre code.hljs` block-level full-width elements, and made each generated `.code-line` span full-width so the line-number grid keeps a usable content column. Reworked the line-number decorator to split highlighted DOM text nodes instead of splitting `innerHTML`, so highlight.js spans that cross newlines are cloned per line instead of corrupting the code block.

## Changed Files

- frontend/src/code-highlight.ts
- frontend/src/styles/base.css
- frontend/src/styles/highlight.css
- src/vaultpub/django_app/static/vaultpub/app.css
- src/vaultpub/django_app/static/vaultpub/app.js

## Tests

- `cd frontend && npm run build`
- `source /data/p/anaconda3/bin/activate base >/dev/null 2>&1 || true; export PATH=/data/p/bin:$PATH; /data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py`

## Manual Verification

- Rendered the affected note source through `vaultpub.core.parser.markdown.render_markdown` and confirmed the `Download files` section remains a single fenced Python code block.
- Checked the packaged `app.css` contains full-width rules for `pre code`, `pre code.hljs`, and `pre code .code-line`.
- Served the rebuilt static folder locally and opened a temporary page containing the affected `Download files` code block with `/usr/bin/chromium-browser --headless`; confirmed 156 numbered code lines, valid `hljs-string` markup across the triple-quoted query, and no literal broken span markup.
- Checked the live `/static/vaultpub/app.js` served from `http://10.110.120.1:9000` contains the DOM-based splitter and no longer contains the old `innerHTML` newline splitter.
