# Feature: Callout Markdown and theme contrast

## Goal

Render standard Markdown inside Obsidian callouts and ensure every callout type has a readable theme-aware default background.

## Conclusion

Callout titles now use inline Markdown and callout bodies use block Markdown before the existing sanitization and external-link processing. Unmapped callout types now fall back to the note theme colors instead of a hard-coded light background.

## Changed Files

- `src/vaultpub/core/parser/markdown.py`
- `src/vaultpub/core/parser/callouts.py`
- `src/vaultpub/core/render/renderer.py`
- `frontend/src/styles/callouts.css`
- Callout renderer and static-asset regression tests

## Tests

- Focused callout and renderer pytest tests
- Full pytest suite
- Ruff and frontend bundle build

## Manual Verification

- In a dark theme, info callouts use the note-color background and retain readable text.
- Callout lists, bold text, and external links render as HTML rather than literal Markdown.
