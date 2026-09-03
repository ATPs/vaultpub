# Feature: Dynamic portal adapter controls

## Goal

Allow host Django portals to expose multi-note slide payloads and suppress the order-editor action for read-only audiences.

## Conclusion

Added dynamic slide-payload rendering and an optional, backward-compatible order-editor visibility flag for dynamic home and page rendering. Cached VaultPub state remains independent of the request-specific visibility choice.

## Changed Files

- `src/vaultpub/django_app/views.py`
- `tests/django/test_django_app.py`

## Tests

- Focused Django adapter tests

## Manual Verification

- Covered by the host portal integration verification.
