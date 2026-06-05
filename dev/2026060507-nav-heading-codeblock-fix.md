# Feature: nav heading codeblock fix

## Goal

Prevent lines starting with `#` inside fenced code blocks from being treated as note headings, and switch the left navigation expand/collapse-all controls from text buttons to icon buttons with hover labels.

## Conclusion

Updated heading extraction to skip protected markdown regions, including fenced code blocks, so code samples no longer leak into the note heading list or TOC. Changed the left sidebar bulk controls to icon-only `+` and `-` buttons with `title` and `aria-label` text for hover and accessibility.

## Changed Files

- `src/vaultpub/core/parser/obsidian_links.py`
- `src/vaultpub/core/index/indexer.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/core/render/templates.py`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/unit/test_indexer.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_indexer.py tests/unit/test_obsidian_links.py tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`
- `cd frontend && npm run build`

## Manual Verification

- Open a note with fenced code containing `#` and confirm those lines do not appear in the TOC or topbar current heading.
- Hover the `+` button in the left nav and confirm the tooltip says `Expand all`.
- Hover the `-` button in the left nav and confirm the tooltip says `Collapse all`.
