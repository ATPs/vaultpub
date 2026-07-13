# Feature: top folder navigation refinement

## Goal

Make the active top-folder layout use the top-bar context area, omit an empty Root tab, and avoid an unnecessary overflow menu.

## Conclusion

The breadcrumb/current-heading context is hidden while folder tabs are active, allowing the tabs to use the available one-line space. Root appears only when root-level files exist. The overflow menu remains conditional on tabs exceeding that expanded space.

## Changed Files

- `frontend/src/sidebar.ts`
- `frontend/src/styles/layout.css`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`

## Tests

- `npm run build` in `frontend/`

## Manual Verification

- In headless Chromium, enabled the layout on the standard fixture and confirmed the top-bar context has `display: none`, `Root` and `Folder` fit as visible tabs, and the overflow control remains hidden.
- The empty-root case is handled by omitting the `Root` section unless the rendered tree contains a direct root file.
