# Feature: Obsidian global attachment resolution

## Goal

Render Obsidian and Markdown image links that use a bare attachment filename when the attachment is elsewhere in the shared vault.

## Conclusion

Added vault-wide filename lookup for bare attachment targets after direct and relative-path lookup. This lets `![[image.png]]` and `![](image.png)` resolve attachments outside the published note sub-path. Explicit paths still take precedence; duplicate names select the closest attachment directory, then use path order for deterministic behavior.

## Changed Files

- `src/vaultpub/core/render/renderer.py`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`

## Tests

- Added renderer coverage for Obsidian and Markdown bare image syntax.
- Extended ASGI coverage for scoped notes using a vault-root attachment.

## Manual Verification

- Open `2026oral_cancer/20260710 预处理.md` with `--sub-path 2026oral_cancer` and confirm its root-level screenshot embeds render.
