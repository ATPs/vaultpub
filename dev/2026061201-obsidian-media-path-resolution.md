# Feature: obsidian-media-path-resolution

## Goal

Fix page-time media/file rendering for real Obsidian vault content where local paths use percent-escaped names like `%20` and over-deep relative prefixes like `../../../../../attachments/...`.

Verification:
- Requesting a note page dynamically rewrites matching local media/file links to canonical published URLs.
- `%20` in source Markdown resolves to filenames containing spaces.
- Over-deep `../` paths can fall back to `attachments/...` and intermediate parent-relative candidates when the published file exists.
- Search, navigation, graph, and backlinks behavior stays unchanged.

## Conclusion

Implemented the fix in the renderer only.

`Renderer._resolve_target()` now:
- tries URL-decoded and raw path variants
- checks progressively relaxed fallback candidates for file-like local paths with leading `../`
- continues to resolve only against already published notes, text pages, and attachments

This fixed the real `general/通过easytier不受限制访问服务器.md` page images that used `../attachments/Exported%20image...png`.

Intentional non-change:
- `.toml` attachments are still not published under the current config because only default attachment types and `--force-include-regex '.*\\.py$'` are enabled.

## Changed Files

- `src/vaultpub/core/render/renderer.py`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`

## Tests

- `source /data/p/anaconda3/bin/activate base && export PATH=/data/p/bin:$PATH && PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py`

## Manual Verification

- Rendered the real note `general/通过easytier不受限制访问服务器.md` against `/data2/pub/couchdb/obsidian/server_obsidian`.
- Confirmed the three `Exported%20image...png` references now render as `/assets/attachments/Exported image ... .png`.
- Confirmed the old raw `../attachments/...%20...` output no longer appears in rendered HTML.
