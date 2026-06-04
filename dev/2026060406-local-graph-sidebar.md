# Feature: Local Graph Sidebar Gating

## Goal

Stop rendering the sidebar graph placeholder for pages whose local graph has fewer than three nodes. Keep the graph sidebar for pages with a meaningful local note graph, and remove stale placeholders from the DOM on the client if the graph still resolves too small.

## Conclusion

Implemented server-side gating for sidebar graph rendering across the ASGI app, Django app, and static builder. Note pages now prefer local graph availability when `show_local_graph` is enabled, and the graph container is omitted from the HTML when the local graph has fewer than three nodes. The frontend graph loader now reads the optional `data-graph-note-id` attribute, filters the full graph down to that note's local subgraph, and removes the container from the DOM if the graph is still too small.

## Changed Files

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `src/vaultpub/django_app/templates/vaultpub/partials/graph.html`
- `frontend/src/graph.ts`
- `src/vaultpub/django_app/static/vaultpub/app.js`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/integration/test_web_app.py tests/django/test_django_app.py`
- `npm run build` in `frontend/`

## Manual Verification

- Verified note pages with a meaningful local graph still render a `#graph-container` with `data-graph-note-id`.
- Verified note pages with fewer than three local graph nodes omit `#graph-container` from the HTML response.
- Rebuilt the frontend bundle so the checked-in `app.js` matches the TypeScript change.
