# Feature: obsidian-linked-file-embeds

## Goal

Support Obsidian wiki file links and embeds for referenced vault files that are not part of the default attachment scan, especially cases like:

- `![[../attachments/config.toml]]`
- `[[../attachments/config.toml]]`

Verification:
- page-time rendering resolves these targets using the same decoded and parent-fallback path logic already used for local media
- embedded UTF-8 text files render inline as code blocks
- linked files resolve to canonical `/assets/...` URLs
- ASGI, Django, and static build all keep those generated asset URLs working
- search, navigation, graph, and backlinks remain unchanged

## Conclusion

Implemented dynamic referenced-file resolution in the renderer.

When an Obsidian wiki link/embed target is not found in the existing note, text-page, or attachment index, the renderer now:
- checks the real vault filesystem for a safe matching file
- creates a dynamic text-page view for UTF-8 text files such as `.toml`
- creates a dynamic asset view for non-text files

This lets `![[../attachments/9a6940e3-70d3-43f2-8154-fd376b49d017.toml]]` render as an inline TOML code embed and also exposes the file at `/assets/attachments/...toml` for page and static usage.

Runtime asset serving was updated so `/assets/...` can serve these dynamically referenced files after a page render has registered them. Static build now copies dynamically referenced text/asset files into `assets/` as well.

## Changed Files

- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/core/export/static_builder.py`
- `tests/unit/test_renderer.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `source /data/p/anaconda3/bin/activate base && export PATH=/data/p/bin:$PATH && PYTHONPATH=src /data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_renderer.py tests/integration/test_web_app.py tests/integration/test_static_builder.py tests/django/test_django_app.py`

## Manual Verification

- Rendered the real note `general/通过easytier不受限制访问服务器.md` from `/data2/pub/couchdb/obsidian/server_obsidian`.
- Confirmed `![[../attachments/9a6940e3-70d3-43f2-8154-fd376b49d017.toml]]` no longer renders as unresolved content.
- Confirmed the rendered HTML contains `data-embed-source="/assets/attachments/9a6940e3-70d3-43f2-8154-fd376b49d017.toml"` and `class="language-toml"`.
