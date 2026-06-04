# vaultpub

Publish a local Obsidian vault as a browsable, searchable web site.

vaultpub is **not** an Obsidian Publish client. It does not require an Obsidian account, subscription, or official servers. It works entirely locally with your vault files.

📖 **[Full User Guide →](help/guide.md)**

## Quick Start

```bash
pip install vaultpub
vaultpub serve --vault ~/my-vault --port 8008
# Open http://127.0.0.1:8008
```

## Features

- Browse Obsidian vaults as web pages
- Wikilinks (`[[Note]]`, `[[Note|display]]`, `[[Note#heading]]`)
- Backlinks, tags, and interactive graph
- Full-text client-side search (Ctrl+K)
- Callouts, embeds, and Obsidian-flavored Markdown
- Mermaid diagrams and KaTeX math rendering
- Theme toggle (light/dark/system)
- Hover preview for internal links
- Mobile-responsive layout
- Static site export (`vaultpub build`)
- Django reusable app (`vaultpub.django_app`)
- Real-time updates on file changes (SSE/watchfiles)

## Commands

```bash
# Start development server
vaultpub serve --vault ~/Vault --host 127.0.0.1 --port 8008

# Build static site
vaultpub build --vault ~/Vault --out ./public --clean --base-url https://notes.example.com

# Export vault index as JSON
vaultpub index --vault ~/Vault --json ./index.json

# Diagnose vault issues
vaultpub doctor --vault ~/Vault

# Create config file
vaultpub init --vault ~/Vault
```

## Configuration

Create a `.vaultpub.yml` in your vault root (or specify via `--config`):

```yaml
vault_path: .
site:
  name: My Knowledge Base
  title: My KB
  description: Personal notes
  url: https://notes.example.com
publish:
  mode: publish_false_hides
  exclude_folders: [.obsidian, .git, private]
rendering:
  html_safe_mode: true
  enable_mermaid: true
  enable_math: true
  enable_callouts: true
features:
  navigation: true
  search: true
  graph: true
  toc: true
  backlinks: true
  hover_preview: true
  theme_toggle: true
realtime:
  enabled: true
  debounce_ms: 150
```

### Environment Variables (Perlite-compatible)

| Variable | Config |
|----------|--------|
| `NOTES_PATH` | `vault_path` |
| `SITE_TITLE` | `site_title` |
| `SITE_URL` | `site_url` |
| `SITE_DESC` | `site_description` |
| `HOME_FILE` | `home_file` |
| `SHOW_TOC` | `show_toc` |
| `HTML_SAFE_MODE` | `html_safe_mode` |

## Django Integration

```python
# settings.py
INSTALLED_APPS += ["vaultpub.django_app"]

VAULTPUB = {
    "default": {
        "vault_path": "/srv/notes",
        "url_prefix": "/notes/",
        "home_file": "README",
    }
}
```

```python
# urls.py
from django.urls import include, path
urlpatterns = [path("notes/", include("vaultpub.django_app.urls"))]
```

`url_prefix` should match the `include()` mount path, so rendered note links and API URLs stay under the Django route prefix.

### Django Template Customization

Override any template by placing a file with the same path in your project's `templates/vaultpub/` directory. See the **[User Guide → Django Integration](help/guide.md#template-customization)** for the full context variable reference and examples.

## Python API

```python
from vaultpub import PublisherConfig
from vaultpub.web import create_app

config = PublisherConfig(vault_path="/srv/notes")
app = create_app(config)
```

```python
from vaultpub.export import StaticSiteBuilder
builder = StaticSiteBuilder(config)
builder.build(out_dir="./public", clean=True)
```

## Security

- Path traversal protection: vault-relative paths only
- Hidden files, `.obsidian/`, `.git/`, `private/` excluded by default
- Raw HTML sanitized via bleach in safe mode
- External links get `rel="noopener noreferrer" target="_blank"`
- `metadata.json`, `.vaultpub.yml` never served publicly
- Content Security Policy: Configure your reverse proxy with:
  ```
  default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:
  ```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
ruff format .
```

Python package builds run the frontend bundle automatically through the Hatch build hook.
For manual frontend builds, run `npm run build` in `frontend/`; it installs dependencies, writes
`src/vaultpub/django_app/static/vaultpub/`, and removes `frontend/node_modules` when done.

## License

MIT
