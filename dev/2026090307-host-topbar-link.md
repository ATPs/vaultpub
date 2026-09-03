# Feature: Host Top-Bar Link

## Goal

Allow a host Django project to provide an optional link before the VaultPub title in the top bar.

## Conclusion

The Django base template now accepts a structured `vaultpub_topbar_link` context variable with `url`, `label`, and optional `title` keys. The link is omitted when the variable is absent, so existing integrations retain their current layout.

## Changed Files

- `src/vaultpub/django_app/templates/vaultpub/base.html` - render the optional leading link.
- `frontend/src/styles/layout.css` - style the link as a compact top-bar control.
- `tests/django/test_django_app.py` - cover rendering and placement before the vault title.
- `README.md` - document the new template context variable.

## Tests

- `pytest tests/django/test_django_app.py -q`: 24 passed.
- `npm run build`: passed and generated the packaged link styles.
- xcWebServer `manage.py test vaultpub_portal.tests --settings=xcWebServer.test_settings`: 35 passed.
- xcWebServer `manage.py check --settings=xcWebServer.test_settings`: passed.

## Manual Verification

- xcWebServer supplies a `Vault List` link to `/database/vaultpub/` through its existing global context processor only for authenticated registered-vault viewers who satisfy the centralized vault-list permission.
- Anonymous pages, temporary-share pages, and users without vault-list permission omit the link.
- The focused portal response test verifies that the link renders before the `Lab Notes` vault title.
- A local xcWebServer development server started successfully on `127.0.0.1:9002`; anonymous live requests redirect to login, so no authenticated browser inspection was performed.
