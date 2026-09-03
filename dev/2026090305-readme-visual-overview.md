# Feature: README visual overview

## Goal

Make the README introduce VaultPub through real screenshots and short recordings while preserving the detailed reference documentation. Use a reproducible, privacy-safe showcase vault and keep the media small enough for GitHub.

## Conclusion

Added a visual-first README opening with highlights and a See It in Action section. Added a synthetic Atlas Research showcase vault covering linked Markdown, tags, callouts, Mermaid, KaTeX, code, tables, attachments, backlinks, graph data, and Slide View. Captured and optimized desktop, mobile, search/hover-preview, and Slide View media from the live standalone server. No application code or public API behavior changed.

## Changed Files

- `README.md`
- `docs/showcase-vault/`
- `docs/assets/readme/vaultpub-overview.png`
- `docs/assets/readme/vaultpub-mobile.png`
- `docs/assets/readme/vaultpub-search.gif`
- `docs/assets/readme/vaultpub-slides.gif`

## Tests

- `vaultpub doctor --vault docs/showcase-vault` — passed: 5 notes, 1 attachment, no broken links or duplicate stems.
- `vaultpub build --vault docs/showcase-vault --out <temporary-directory> --clean` — passed: 8 pages built.
- README media-reference existence check — passed for all 4 assets.
- `git diff --check` — passed.
- Media inspection with `file`, `ffprobe`, and representative extracted GIF frames — passed.

## Manual Verification

- Served the showcase vault from the repository source in tmux and confirmed the home page and Slide View route return HTTP 200.
- Captured the desktop overview, 480x844 mobile drawer, search/results/hover-preview flow, and Slide View navigation/grid through Chromium DevTools Protocol.
- Chromium required its profile and crash data under `/dev/shm` to avoid the environment's Crashpad I/O failure; representative frames were inspected for readable content, stable framing, and no overlapping controls.
