# Feature: top folder collapse scope

## Goal

Keep the selected top-level folder visible when using Expand all or Collapse all in the move-folders-to-top-bar layout. Only folders inside the selected top-bar section should be treated as collapsible tree levels.

## Conclusion

Scoped bulk tree actions in the top-folder layout to descendant folders inside the selected section. The selected top-level folder remains open as the structural container for the sidebar, so Collapse all no longer makes the sidebar tree disappear. The normal sidebar folder layout still expands and collapses the full tree.

## Changed Files

- `frontend/src/sidebar.ts`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `dev/2026080701-top-folder-collapse-scope.md`

## Tests

- `npm run build` in `frontend/`
- Browser DOM verification for normal and top-folder layouts

## Manual Verification

- Enable Move folders to top bar, select a top-level folder containing nested folders, and click Collapse all. Confirm the selected top-level folder's contents remain visible while its descendant folders close.
- Click Expand all and confirm descendant folders reopen.
- Disable Move folders to top bar and confirm Collapse all still closes top-level folders.
