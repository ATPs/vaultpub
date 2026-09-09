# Feature: Single Markdown input

## Goal

Allow VaultPub commands to publish one existing Markdown file without exposing
the rest of its containing directory. Referenced non-Markdown resources must be
direct siblings of the selected note.

## Conclusion

`serve`, `build`, `index`, and `doctor` now accept an existing `.md` file for
`--vault`. File input becomes an exact entry-file scope rooted at its parent
directory. Only that note is indexed; its explicitly referenced direct-sibling
resources are registered during rendering and are the only related files served
or copied. Directory publication and `--sub-path` behavior remain unchanged.

## Changed Files

- `src/vaultpub/core/config.py`
- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/cli/main.py`
- `README.md`
- Single-file unit and integration tests

## Tests

- Focused config, scanner, renderer, CLI, static-builder, and web tests
- Full pytest suite
- Ruff checks for the changed files
- `git diff --check`

## Manual Verification

- Not performed; live and static behavior are covered with the ASGI test client
  and static output assertions.
