# Plan: regex-based force-include and force-exclude patterns

## Goal

Allow advanced users to define regular expression patterns that:

- exclude files or folders from public rendering and public access
- force-include additional text files for public rendering beyond the default Markdown-only note set

This is additive to the current behavior:

- Hidden files and hidden folders stay excluded by default.
- Always-forbidden paths such as `.git`, `.obsidian`, `.vaultpub.yml`, and `metadata.json` stay non-public.
- Existing `exclude_folders` and `exclude_globs` remain supported.
- `force_include_regexes` defaults to none.
- `force_exclude_regexes` defaults to none.

## Current State

- Hidden names are already excluded during scan by default in `src/vaultpub/core/scanner.py`.
- Hidden path access is already blocked by default in `src/vaultpub/core/security.py`.
- Notes are currently discovered from `.md` files only.
- Non-Markdown files are currently treated only as attachments when their extension is in `allowed_attachment_types`.
- There is test coverage for hidden paths in:
  - `tests/unit/test_scanner.py`
  - `tests/unit/test_security.py`
- Config already supports:
  - `publish.exclude_folders`
  - `publish.exclude_globs`
- Realtime watching currently skips hidden and excluded-folder paths, but not force include/exclude regex rules because that feature does not exist yet.
- Web and Django note-page routing already checks public visibility, but this logic should be centralized before adding another exclude mechanism.

## Proposed Config

Add a new config field:

```python
force_include_regexes: tuple[str, ...] = ()
force_exclude_regexes: tuple[str, ...] = ()
```

YAML shape:

```yaml
publish:
  force_include_regexes:
    - ".*\\.py$"
    - "scripts/.*/Dockerfile$"
  force_exclude_regexes:
    - "(^|/)secret(/|$)"
    - "\\.private\\.(md|png)$"
```

Rules:

- Patterns match against the normalized vault-relative POSIX path, for example `Folder/Note.md`.
- Matching uses regex search semantics, not exact full-string matching.
- Force-include regexes default to empty.
- Force-exclude regexes default to empty.
- Force-include regexes expand the set of renderable source files beyond `.md`.
- Force-exclude regexes apply to both notes and attachments.
- `force_exclude_regexes` wins over `force_include_regexes` when both match the same path.
- Neither force rule bypasses always-forbidden paths or hidden-path defaults.
- Invalid regex patterns should raise `ConfigError` during configuration/setup, not fail later during scanning or requests.

Regex syntax note:

- The regex equivalent of a glob like `*.py` is `.*\\.py$`.
- A pattern like `*\\.py` should be treated as invalid regex and rejected during config validation.

## Force-Include Rendering Model

Force-included files need explicit behavior because they are not Markdown notes today.

Recommended first pass:

- Limit force-include to text files that can be decoded as UTF-8 or UTF-8-SIG.
- Render force-included non-Markdown files as plain text code pages using `<pre><code>`.
- Infer the code language from the file extension when possible, for example `.py` -> `language-python`.
- Use filename as the page title by default.
- Include them in navigation and search.
- Do not treat them as Obsidian Markdown:
  - no frontmatter publish rules
  - no wikilink parsing
  - no backlinks or graph edges unless later extended

This keeps the first implementation small and predictable.

## Visibility Model

Unify path visibility checks in one shared helper so scanner, runtime routes, and realtime watcher use the same rules.

Suggested evaluation order:

1. Block always-forbidden names.
2. Block hidden files and folders by default unless `hidden_file_access=True`.
3. Apply `exclude_folders`.
4. Apply `exclude_globs`.
5. Apply `force_exclude_regexes`.
6. Decide whether the file is renderable:
   - `.md` files are renderable by default
   - non-Markdown text files are renderable only when matched by `force_include_regexes`
7. Apply frontmatter publish mode rules for markdown notes only.

This avoids duplicating partial logic in:

- `src/vaultpub/core/scanner.py`
- `src/vaultpub/core/security.py`
- `src/vaultpub/core/realtime/watcher.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/django_app/views.py`

## Implementation Plan

### 1. Config and validation

- Add `force_include_regexes` to `PublisherConfig`.
- Add `force_exclude_regexes` to `PublisherConfig`.
- Load it from `publish.force_include_regexes` in YAML.
- Load it from `publish.force_exclude_regexes` in YAML.
- Decide whether to expose an environment variable.
- Validate/compile patterns once during config setup or scanner initialization.

Recommended first pass: no environment variable yet. YAML is enough for this feature and keeps the surface smaller.

### 2. Shared path-policy matcher

- Introduce a shared helper for normalized-path inclusion and exclusion checks.
- Make the helper reusable for:
  - directory pruning during scan
  - file filtering during scan
  - request-time public access checks
  - realtime watcher filtering

Important detail:

- Directory matching must work for both exact directory names and path prefixes, so a pattern that force-excludes a folder also excludes its descendants.

### 3. Renderable-file classification

- Add one clear classification step that answers:
  - excluded entirely
  - render as Markdown note
  - render as force-included text page
  - keep as attachment
  - ignore
- Ensure force-included files are only accepted when text-decoding succeeds.
- Keep binary files out of the rendered-page path even if a regex accidentally matches them.

### 4. Scanner integration

- Keep current hidden-path defaults unchanged.
- Prune directories as early as possible when they match folder, glob, or force-exclude regex rules.
- Skip matching files before note or attachment ingestion.
- Ingest `.md` files as today.
- Ingest force-included text files as additional renderable pages.
- Ensure attachments under force-excluded regex paths never enter `attachments_by_path`.

### 5. Route and API enforcement

- Use the shared visibility helper in standalone web routes.
- Use the same helper in Django views.
- Apply it to:
  - note pages
  - force-included text pages
  - note API endpoints
  - attachment endpoints

This prevents drift between “not indexed” and “not publicly accessible”.

### 6. Realtime behavior

- Update the watcher filter so changes under force-excluded paths do not trigger public index updates.
- Ensure changes to force-included files trigger the same rebuild/update path as Markdown notes.
- Keep temp/swap-file skips unchanged.

### 7. Docs and defaults

- Update `README.md`.
- Update `help/guide.md`.
- Update the generated `.vaultpub.yml` template in `src/vaultpub/cli/main.py`.
- Document clearly that hidden files and hidden folders are already excluded by default.
- Document that `force_include_regexes` is empty by default.
- Document that `force_exclude_regexes` is empty by default.
- Document that the regex form of `*.py` is `.*\\.py$`.
- Document the first-pass rendering behavior for force-included text files.

## Test Plan

Add or update tests for:

- config loading of `publish.force_include_regexes`
- config loading of `publish.force_exclude_regexes`
- invalid regex raises a configuration error
- file force-exclusion by regex
- folder force-exclusion by regex
- attachment force-exclusion by regex
- non-Markdown text file inclusion by regex
- force-included `.py` file appears in nav and search
- force-included file renders as plain text code page
- non-text file matched by force-include regex is rejected safely
- force-exclude wins when a file matches both force-include and force-exclude regexes
- hidden files remain excluded by default without any regex config
- `hidden_file_access=True` still does not bypass force-excludes
- `hidden_file_access=True` does not make force-include override force-exclude
- direct web access to force-excluded notes returns not found
- direct web access to force-excluded attachments returns not found
- direct web access to force-included text pages works
- Django note/API/attachment access respects force-excludes
- Django rendering/access respects force-included text pages
- realtime watcher ignores force-excluded changes
- realtime watcher handles force-included text-file changes

## Manual Verification

Use a vault with examples like:

- `private/Note.md`
- `research/secret-plan.md`
- `images/diagram.private.png`
- `.hidden/secret.md`
- `scripts/tool.py`

Verify:

- `.hidden/secret.md` is still excluded by default without any new config.
- A force-exclude regex can exclude `research/secret-plan.md` while leaving nearby notes public.
- A force-exclude regex can exclude `images/diagram.private.png` from public asset serving.
- `force_include_regexes: [".*\\.py$"]` publishes `scripts/tool.py`.
- `scripts/tool.py` renders as a code/text page rather than being treated as Markdown.
- A path matched by both force-include and force-exclude stays excluded.
- Force-matched paths still cannot expose `.git`, `.obsidian`, or hidden default paths.
- Force-excluded paths do not appear in nav, search, graph, backlinks, APIs, or static output.

## Out of Scope

- Replacing `exclude_globs` with regexes.
- Force-include or force-exclude overriding hidden or always-forbidden paths.
- Full Obsidian parsing for force-included non-Markdown files.
- Different regex rules for notes vs attachments beyond the basic include/exclude policy above.
- UI for editing exclude patterns.
