# Feature: Review Fix Guidance

## Goal

Record the review findings against `dev/20260603init.plan.dev.md` and provide concrete development guidance for the next AGENTS round.

This document is not an implementation record. It is a handoff note for fixing the gaps found after the initial implementation.

## Review Conclusion

The project has a working v0.1-alpha skeleton: package layout, CLI entrypoint, scanning, partial indexing, ASGI/Django entrypoints, static build basics, pytest, and ruff are in place.

It does not yet satisfy the full development goal in `dev/20260603init.plan.dev.md`. The largest gaps are Obsidian syntax rendering, realtime updates, static export completeness, permalink/alias routing, frontend wiring, and mypy/CI acceptance.

## Verification Performed

- `/data/p/anaconda3/envs/django/bin/python -m pytest`
  - Result: 73 passed, 3 warnings.
- `/data/p/anaconda3/envs/django/bin/python -m ruff check .`
  - Result: passed.
- `/data/p/anaconda3/envs/django/bin/python -m mypy src`
  - Result: failed with 66 errors across 20 files.
- Static build smoke test with `tests/fixtures/vault_links`
  - Result: generated note pages, `index.html`, `search-index.json`, `graph.json`, `robots.txt`.
  - Missing expected outputs: tag pages, RSS, frontend static asset copy, `publish.css`/trusted `publish.js`.
- Renderer smoke check with `tests/fixtures/vault_obsidian_syntax`
  - Result: embeds/callouts were escaped as text under default safe mode; Mermaid remained a code block; Math remained raw `$...$`.

## Blocking Issues To Fix

### 1. Obsidian Syntax Rendering Is Not Actually Working

Relevant files:

- `src/vaultpub/core/render/renderer.py`
- `src/vaultpub/core/parser/markdown.py`
- `src/vaultpub/core/render/sanitize.py`
- `src/vaultpub/core/parser/callouts.py`
- `src/vaultpub/core/parser/embeds.py`
- `src/vaultpub/core/parser/math.py`
- `src/vaultpub/core/parser/mermaid.py`

Current behavior:

- `Renderer.render_note()` replaces wikilinks/callouts with raw HTML before calling markdown-it.
- Default `html_safe_mode=True` makes markdown-it escape inserted raw HTML.
- Output examples from fixture checks:
  - `![[image.png|300]]` becomes visible escaped text like `&lt;img ...&gt;`.
  - callout `<div class="callout"...>` becomes escaped paragraph text.
  - Mermaid stays as `<pre><code class="language-mermaid">...`.
  - Math stays as raw `$...$` and `$$...$$`.

Implementation guidance:

- Keep markdown parsing on `markdown-it-py`; do not hand-render whole Markdown with regex.
- Use one of these safe approaches consistently:
  - Prefer markdown-it plugin/token rules for wikilinks, embeds, callouts, Mermaid, and Math.
  - Or use protected placeholders before Markdown render, then replace placeholders after Markdown render and run final sanitization.
- Final HTML must pass through `sanitize_html()` when `html_safe_mode=True`.
- After sanitization, apply `add_external_link_attrs()` so external links get `rel="noopener noreferrer"` and `target="_blank"`.
- Render normal internal wikilinks as anchors with `class="internal-link"` so hover preview can match them.
- Render broken links as:

```html
<a class="internal-link is-unresolved" data-target="Missing">Missing</a>
```

- Render image embeds as real `<img>` with optional `width`/`height`.
- Render audio/video/PDF embeds using the helpers in `parser/embeds.py`.
- Render note embeds as embedded HTML with circular embed protection and a max depth of 5.
- Render Mermaid fenced blocks as:

```html
<div class="mermaid">graph TD...</div>
```

- Render Math to `.math.inline` and `.math.block` wrappers, or adapt frontend math init to support raw delimiters. Prefer backend wrappers because `frontend/src/math-init.ts` already expects `.math`.

### 2. Realtime Updates Are Functionally Broken

Relevant files:

- `src/vaultpub/core/realtime/watcher.py`
- `src/vaultpub/core/realtime/broadcaster.py`
- `src/vaultpub/web/app.py`
- `src/vaultpub/web/sse.py`
- `src/vaultpub/web/routes.py`
- `frontend/src/realtime.ts`

Current behavior:

- `_classify_changes()` calls `os.PathLike(path_str)`, which is invalid and gets swallowed by `except Exception`, so most changes produce no event.
- `_apply_changes()` calls `indexer.build()` but discards the returned `VaultIndex`; `AppState.index` and `AppState.renderer` are not updated.
- `SSEBroadcaster.stream()` calls `request_disconnected()` without `await`.
- Frontend polling fallback requests `/api/events/version`, but no route exists.

Implementation guidance:

- Convert watchfiles paths with `Path(path_str)` and compare against `Path(root)`.
- Accept watchfiles `Change` enum values directly instead of assuming integer values.
- On any valid Markdown/attachment change, rebuild a new `VaultIndex` for correctness in this phase.
- Replace `AppState.index` and `AppState.renderer` atomically after rebuild.
- Keep full rebuild for now; true incremental indexing can remain deferred.
- Fix SSE disconnect handling by accepting `Callable[[], Awaitable[bool]]` and awaiting it.
- Add `/api/events/version` returning the current EventBus version, or remove polling fallback from frontend. Prefer adding the route because the frontend already expects it.
- Event payload should match the plan:

```json
{
  "type": "index.changed",
  "version": 42,
  "changed": [{"kind": "note", "path": "README.md", "url": "/README", "change": "modified"}],
  "deleted": [],
  "graph_changed": true,
  "nav_changed": false,
  "search_changed": true
}
```

### 3. Static Export Is Incomplete

Relevant files:

- `src/vaultpub/core/export/static_builder.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/static/vaultpub/app.css`
- `src/vaultpub/django_app/static/vaultpub/app.js`

Current behavior:

- Build emits note pages, home page, attachments, `search-index.json`, `graph.json`, conditional `sitemap.xml`, and `robots.txt`.
- Missing plan requirements:
  - tag pages
  - RSS
  - frontend static assets under `static/vaultpub/`
  - `publish.css`
  - trusted-mode `publish.js`
  - sitemap when `site_url` is absent should be a deliberate documented choice; current behavior silently skips it.

Implementation guidance:

- Always copy bundled `app.css` and `app.js` into `public/static/vaultpub/`.
- Static page templates must reference copied assets with paths that work in static hosting.
- Generate tag pages at `tags/<tag-path>/index.html`.
- Generate `rss.xml` from published notes sorted by mtime, using frontmatter date later if available.
- Generate `sitemap.xml` when `site_url` is set. If not set, either skip with a recorded warning in `BuildResult.errors` or emit relative URLs only if tests/documentation are updated. Prefer warning + skip.
- Copy `publish.css` from vault root if present.
- Do not copy `publish.js` unless a trusted mode/config flag exists and is true. Add a config field only if needed; default must remain disabled.

### 4. Permalink And Alias Routing Do Not Meet The Plan

Relevant files:

- `src/vaultpub/core/index/indexer.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/core/export/static_builder.py`

Current behavior:

- `VaultIndex.permalinks` records `permalink -> note_id`.
- `VaultIndex.redirects` records `default_url -> permalink`.
- Web route only matches `note.url_path` and then checks redirects.
- Result: default URL may redirect to permalink, but permalink URL itself returns 404.
- Alias redirects are not generated.

Implementation guidance:

- Treat canonical URL as:
  - permalink, if present;
  - otherwise `note.url_path`.
- Route resolution must support:
  - canonical note URL -> render note.
  - default URL when permalink exists -> 301 to permalink.
  - alias URL -> 301 to canonical URL.
- Keep note `url_path` stable for internal IDs if simpler, but expose helper methods/maps for public canonical paths.
- Static export must write canonical pages and redirect pages or static redirect HTML for default/alias URLs.
- Doctor must report duplicate aliases and duplicate permalinks.

### 5. Tags, Inline Tags, And Graph Are Partial

Relevant files:

- `src/vaultpub/core/index/indexer.py`
- `src/vaultpub/core/parser/obsidian_links.py`
- `src/vaultpub/core/models.py`

Current behavior:

- Frontmatter tags are indexed.
- Inline tags in Markdown body are not merged into `NoteRecord.tags`.
- Graph creates tag edges but no tag nodes, producing dangling graph edges.

Implementation guidance:

- Use `find_inline_tags()` during note parsing.
- Merge inline tags with frontmatter tags.
- Normalize tag comparison to lowercase; display can preserve original value where practical.
- Add graph nodes for every tag:

```json
{"id": "tag:project/demo", "label": "#project/demo", "group": "tag"}
```

- Add tests for nested tags and non-tags such as `#123`.

### 6. Frontend Features Are Not Wired Into Templates

Relevant files:

- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/templates/vaultpub/base.html`
- `frontend/src/search.ts`
- `frontend/src/preview.ts`
- `frontend/src/graph.ts`
- `frontend/src/theme.ts`
- `frontend/src/realtime.ts`

Current behavior:

- Frontend modules exist, but server templates do not expose enough DOM hooks.
- Search only opens from Ctrl/Cmd+K or elements matching `[data-action='search']` / `.search-trigger`; templates do not include a visible trigger.
- Hover preview only matches `a.internal-link`; normal rendered wikilinks currently do not get this class.
- Graph needs `#graph-container`; core template does not include it.
- Realtime checks `body[data-realtime="false"]`, but templates do not set this attribute.
- Core template contains literal `{% toc %}` and `{% backlinks %}` text in the right sidebar.

Implementation guidance:

- Add a simple top bar with:
  - site name/logo area
  - search trigger
  - theme toggle button with `id="theme-toggle"`
  - mobile nav button if mobile drawer is kept
- Add `data-realtime="true|false"` to `<body>`.
- Add graph container only when `config.show_graph` or `config.show_local_graph` is true.
- Ensure normal internal links use `class="internal-link"`.
- Remove literal template placeholders from non-Django core template.
- Keep server-rendered HTML usable without frontend; frontend should enhance behavior only.

### 7. Publish Filtering And Hidden Access Need A Clear Policy

Relevant files:

- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/security.py`
- `src/vaultpub/core/config.py`

Current behavior:

- `os.walk` prunes hidden and excluded directories before reading notes.
- `hidden_file_access=True` cannot expose notes inside hidden folders because hidden directories are still pruned.
- `publish: true` cannot override excluded folders because excluded folders are never scanned.

Implementation guidance:

- Decide and implement this policy:
  - Default: excluded folders and hidden folders stay hidden.
  - `hidden_file_access=True` allows hidden folders/files except always-forbidden paths such as `.git`, `.obsidian`, `.vaultpub.yml`, `.obsidian-publish.yml`, and `metadata.json`.
  - `publish: true` may override excluded folders only when `publish_property_mode == "publish_true"` or when a new explicit config flag is added. Prefer avoiding a new flag for now and only allow the override in `publish_true` mode.
- Scanner must read candidate notes before deciding override behavior.
- Public attachment access must remain limited to indexed allowed attachments.

### 8. Typing And CI Acceptance Are Not Complete

Relevant files include:

- `src/vaultpub/core/config.py`
- `src/vaultpub/core/index/indexer.py`
- `src/vaultpub/core/render/sanitize.py`
- `src/vaultpub/core/realtime/*.py`
- `src/vaultpub/web/*.py`
- `src/vaultpub/django_app/*.py`
- `src/vaultpub/cli/main.py`

Current behavior:

- `mypy src` fails with 66 errors.

Implementation guidance:

- Add missing type stubs where appropriate:
  - `types-PyYAML`
  - `types-bleach`
  - Django stubs only if the project wants strict Django typing; otherwise configure mypy overrides for Django imports.
- Replace raw `dict` with typed aliases or concrete dataclasses where reasonable.
- Fix real type bugs, especially:
  - `note.blocks[block_id] = None` despite `dict[str, BlockRef]`.
  - `SSEBroadcaster.stream()` return type should be `AsyncGenerator[str, None]`.
  - `callable` should be `Callable`.
  - `object` parameters passed where `NoteRecord` is required.
- Keep `mypy` strict if practical; otherwise document targeted overrides in `pyproject.toml`.

## Development Order

Use this order to avoid building on broken behavior:

1. Add failing tests for renderer output, permalink/alias routes, static export outputs, realtime event classification, inline tags, graph tag nodes, and `doctor` duplicate reporting.
2. Fix renderer pipeline and sanitize behavior.
3. Fix route canonicalization for permalink/alias.
4. Fix indexer tags/graph/search/backlinks data.
5. Fix static export completeness.
6. Fix realtime watcher/SSE/state replacement.
7. Wire frontend hooks into templates and rebuild/copy frontend assets.
8. Fix `mypy src`.
9. Update README and add a new `dev/YYYYMMDDNN-*.md` implementation record describing the completed fixes.

## Required Acceptance Tests

Run these before marking the next implementation complete:

```bash
/data/p/anaconda3/envs/django/bin/python -m pytest
/data/p/anaconda3/envs/django/bin/python -m ruff check .
/data/p/anaconda3/envs/django/bin/python -m mypy src
```

If frontend dependencies are installed:

```bash
cd frontend
npm run build
```

Manual/static checks:

```bash
/data/p/anaconda3/envs/django/bin/python -c 'from vaultpub.cli.main import app; app()' build \
  --vault tests/fixtures/vault_links \
  --out /tmp/vaultpub-review-site \
  --clean \
  --base-url https://notes.example.com
```

Expected static outputs:

- `index.html`
- per-note canonical pages
- redirect pages if permalink/alias are present
- `search-index.json`
- `graph.json`
- `sitemap.xml` when `site_url`/`--base-url` is set
- `rss.xml`
- `robots.txt`
- `tags/<tag>/index.html`
- `static/vaultpub/app.css`
- `static/vaultpub/app.js`

## Out Of Scope For This Fix Round

Unless explicitly requested, do not spend this round on:

- Dockerfile/docker-compose.
- SQLite FTS.
- Canvas preview.
- Full Obsidian plugin execution.
- Trusted `publish.js` by default.
- Full incremental indexing. Full rebuild on changes is acceptable if state updates correctly.

## Assumptions

- Docker remains deferred because the previous dev record says it was omitted by user request.
- Static export should work without server APIs for basic browsing, search, graph, tags, backlinks, Mermaid, and Math.
- Security defaults must remain conservative: hidden/private/config/raw metadata files are not public unless an explicit safe rule says otherwise.
