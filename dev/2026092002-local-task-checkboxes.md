# Feature: local task-checkbox state

## Goal

Allow Markdown task-list checkboxes to be clicked without sending any state to
VaultPub or another server, while restoring each browser's choice after reload.

## Conclusion

Task-list inputs are now enabled. The frontend stores changed states in
`localStorage` under `vaultpub.taskLists.v1:<pathname>`, using each task's
rendered order and text as its local identity. The state is isolated to the
current browser origin and page path, requires no API or database change, and
is restored for normal pages and task lists added later by Slide View.

## Changed Files

- `src/vaultpub/core/parser/markdown.py`
- `src/vaultpub/core/render/sanitize.py`
- `frontend/src/task-lists.ts`
- `frontend/src/app.ts`
- `frontend/src/styles/base.css`
- Generated VaultPub static assets and rendering/static-asset tests

## Tests

- Focused Markdown, sanitizer, renderer, and static-asset tests.
- `npm run build` in `frontend/`.
- Full pytest suite, Ruff, and `git diff --check`.

## Manual Verification

- On the supplied shared page, toggle a task, reload the same URL, and confirm
  the state is restored locally without a network request that writes task data.
