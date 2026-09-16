# Feature: Hide Temporary Share Vault Slides

## Goal

Prevent temporary VaultPub shares from advertising or serving whole-vault Slide View while retaining scoped note and folder presentations.

## Conclusion

Added a default-enabled dynamic configuration switch that removes whole-vault Slide View launch data when disabled. xcWebServer temporary shares set it to disabled and no longer register a whole-vault slide route.

## Changed Files

- `src/vaultpub/core/config.py`
- `src/vaultpub/django_app/conf.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/web/routes.py`
- `tests/unit/test_config.py`
- `tests/django/test_django_app.py`
- `tests/integration/test_web_app.py`

## Tests

`pytest tests/unit/test_config.py tests/django/test_django_app.py tests/integration/test_web_app.py -q` passed 72 tests. The xcWebServer portal module passed 42 tests, and its VaultPub permission-inventory regression passed.

## Manual Verification

Not performed.
