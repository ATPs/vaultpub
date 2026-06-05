# Feature: unified-local-resource-resolution

## Goal

Make local resources resolve canonically across standalone serve mode, Django mounts, and static export.

Verification targets:
- `![[image.png]]` from a nested note resolves to `/assets/<note-dir>/image.png`
- Standard Markdown local links and images resolve to published note, text-page, or asset URLs
- Force-included text pages can be linked and embedded from notes
- Django mount prefixes and static export rewrites still work

## Conclusion

Implemented a shared canonical attachment URL helper and rewired renderer, scanner, and realtime watcher to use it.

The renderer now:
- resolves Obsidian wikilinks and embeds against the current note directory or vault root
- canonicalizes standard Markdown and raw-HTML `href`/`src` local paths after Markdown rendering
- embeds published text pages as code blocks for `![[file.py]]`-style references

Also updated the Django settings bridge to accept `force_include_regexes` / `force_exclude_regexes`, added fixtures for local-resource coverage, and refreshed README guidance for relative and root-relative local paths.

## Changed Files

- `src/vaultpub/core/paths.py`
- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/realtime/watcher.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/django_app/conf.py`
- `README.md`
- `tests/conftest.py`
- `tests/fixtures/vault_local_resources/README.md`
- `tests/fixtures/vault_local_resources/subdir/README.md`
- `tests/fixtures/vault_local_resources/subdir/Other.md`
- `tests/fixtures/vault_local_resources/subdir/tool.py`
- `tests/fixtures/vault_local_resources/subdir/image.png`
- `tests/fixtures/vault_local_resources/subdir/doc.pdf`
- `tests/fixtures/vault_obsidian_syntax/image.png`
- `tests/fixtures/vault_obsidian_syntax/Other Note.md`
- `tests/unit/test_paths.py`
- `tests/unit/test_regex_rules.py`
- `tests/unit/test_renderer.py`
- `tests/unit/test_realtime_watcher.py`
- `tests/integration/test_web_app.py`
- `tests/integration/test_static_builder.py`
- `tests/django/test_django_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest`

## Manual Verification

- Confirmed the original failure mode now resolves correctly in rendered HTML for nested notes:
  `![[image.png]]` in `subdir/README.md` renders to `/assets/subdir/image.png`
- Confirmed Django-mounted pages prefix canonical asset and text-page URLs under `/notes/`
- Confirmed static build keeps `/assets/...` URLs and rewrites page links to `.html`
