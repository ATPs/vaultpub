# Feature: Obsidian mixed link rendering

## Goal

Render notes that mix ordinary Obsidian wikilinks and image embeds without corrupting later content. Preserve single-line Markdown breaks by default and ensure every table-of-contents entry has a unique heading target.

## Conclusion

Updated wikilink discovery and replacement to use source positions, changed the default line-break mode to preserve soft breaks, and assigned unique suffixes to repeated heading slugs. Standalone ordinary links and media now retain their Markdown paragraph wrappers, while block embeds continue to be unwrapped.

## Changed Files

- src/vaultpub/core/parser/obsidian_links.py
- src/vaultpub/core/render/renderer.py
- src/vaultpub/core/index/indexer.py
- src/vaultpub/core/config.py
- src/vaultpub/cli/main.py
- README.md
- tests/unit/test_obsidian_links.py
- tests/unit/test_markdown.py
- tests/unit/test_config.py
- tests/unit/test_indexer.py
- tests/unit/test_renderer.py

## Tests

- Focused parser, configuration, indexer, renderer, web, and Django test suites.
- Full pytest suite and Ruff checks in the Django environment.

## Manual Verification

- Render the reported 2026oral_cancer/20260811 目前可靠的结果.md note with --sub-path 2026oral_cancer.
- Confirm image embeds, paragraph breaks, and every right-side table-of-contents link render correctly.
