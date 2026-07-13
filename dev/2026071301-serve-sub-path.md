# Feature: serve sub-path

## Goal

Allow `vaultpub serve` to share selected vault directories while retaining access to allowed attachments elsewhere in the vault.

## Conclusion

Added repeatable `--sub-path` support for `serve`. Explicit sub-paths replace YAML folder scope for notes and text pages, while all otherwise-public vault attachments remain available. Omitted sub-paths leave YAML `publish.include_folders` unchanged.

## Changed Files

- `src/vaultpub/cli/main.py`
- `src/vaultpub/core/config.py`
- `src/vaultpub/core/scanner.py`
- `README.md`
- `tests/unit/test_cli.py`
- `tests/unit/test_scanner.py`
- `tests/integration/test_web_app.py`

## Tests

- CLI scope, duplicate, root, and invalid-path coverage.
- Scanner and ASGI integration coverage for scoped notes and vault-wide attachments.

## Manual Verification

- Run `vaultpub serve --vault /data2/pub/couchdb/obsidian/limuyang --sub-path 2026oral_cancer` and open a note that embeds an attachment from the vault root or a parent directory.
