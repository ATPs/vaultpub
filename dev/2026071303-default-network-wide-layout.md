# Feature: network host and wide layout defaults

## Goal

Make `vaultpub serve` reachable on all network interfaces by default and show pages in wide-content mode for new browser preferences.

## Conclusion

Changed the `serve` host default to `0.0.0.0`. Changed the frontend wide-content default to enabled while preserving any explicit `vaultpub.wideContent` value already stored in the browser.

## Changed Files

- `src/vaultpub/cli/main.py`
- `frontend/src/topbar-context.ts`
- `src/vaultpub/django_app/static/vaultpub/`
- `README.md`
- `tests/unit/test_cli.py`

## Tests

- CLI help verifies the all-interface host default.
- Rebuilt the frontend bundle and ran the project test suite.

## Manual Verification

- Run `vaultpub serve --vault /path/to/vault` and open the server's network address from another machine.
- Open a page in a browser without a `vaultpub.wideContent` local-storage value and confirm wide content is enabled.
