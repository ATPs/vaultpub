# Feature: Review Verification Fixes

## Goal

Verify `dev/2026060304-review-fixes.md` against the actual implementation and correct any gaps that remained after that development round.

## Conclusion

The baseline verification in `dev/2026060304-review-fixes.md` was mostly complete, but targeted smoke tests found several missed behaviors:

- Renderer placeholders were still escaped by markdown-it because HTML comment placeholders did not survive safe mode.
- Markdown frontmatter was rendered into page bodies.
- Normal wikilinks did not receive `internal-link`, so hover preview could not match them.
- Note embeds rendered as links instead of embedded note content.
- Static permalink pages redirected in the wrong direction.
- `/api/page/<permalink>` and local graph API did not resolve canonical URLs.
- Callout `data-callout` attributes were stripped by bleach.

These issues were corrected and covered with regression tests.

## Changed Files

- `src/vaultpub/core/render/renderer.py` — safe placeholder tokens, frontmatter stripping, internal link class, recursive note embeds, canonical link targets.
- `src/vaultpub/core/parser/callouts.py` — stop parsing a callout before the next callout block.
- `src/vaultpub/core/render/sanitize.py` — preserve required `data-*` attributes used by callouts and rendered notes.
- `src/vaultpub/core/export/static_builder.py` — write permalink pages as canonical pages and default/alias pages as redirects.
- `src/vaultpub/core/index/indexer.py` — use canonical URLs in graph/search output.
- `src/vaultpub/core/render/seo.py` — use canonical permalink URL in SEO metadata.
- `src/vaultpub/core/security.py` — align hidden file public checks with `hidden_file_access`.
- `src/vaultpub/web/routes.py` — resolve canonical/default/alias URLs for pages, API page, and local graph.
- `src/vaultpub/django_app/views.py` — mirror canonical/default/alias URL resolution for Django views.
- `tests/unit/test_renderer.py` — regression coverage for real Obsidian syntax HTML, frontmatter stripping, note embeds, and internal link classes.
- `tests/integration/test_web_app.py` — permalink/alias page and API behavior.
- `tests/integration/test_static_builder.py` — static permalink canonical output and redirect direction.

## Tests

```bash
/data/p/anaconda3/envs/django/bin/python -m pytest
# 78 passed, 16 warnings

/data/p/anaconda3/envs/django/bin/python -m ruff check .
# All checks passed

/data/p/anaconda3/envs/django/bin/python -m mypy src
# Success: no issues found in 49 source files
```

## Manual Verification

Static permalink smoke test:

```bash
/data/p/anaconda3/envs/django/bin/python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from vaultpub.core.config import PublisherConfig
from vaultpub.core.export import StaticSiteBuilder

with TemporaryDirectory() as tmp:
    root = Path(tmp) / "vault"
    out = Path(tmp) / "public"
    root.mkdir()
    (root / "README.md").write_text("---\npermalink: about\naliases:\n - Old Home\n---\n# Home")
    StaticSiteBuilder(PublisherConfig(vault_path=root, site_url="https://notes.example.com")).build(out, clean=True)
    assert (out / "about" / "index.html").exists()
    assert 'content="0;url=/about"' in (out / "README" / "index.html").read_text()
    assert 'content="0;url=/about"' in (out / "Old Home" / "index.html").read_text()
    assert "https://notes.example.com/about" in (out / "sitemap.xml").read_text()
PY
```

Additional smoke checks verified:

- Obsidian syntax renders real HTML for image embeds, callouts, Mermaid, and Math.
- `search_documents` and graph nodes use permalink canonical URLs.
- `hidden_file_access=True` allows indexed hidden notes except always-forbidden paths.
- `publish_property_mode="publish_true"` can publish `publish: true` notes from excluded folders.
