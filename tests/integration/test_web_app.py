"""Integration tests for the ASGI web app."""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from vaultpub.core.config import PublisherConfig
from vaultpub.web import create_app


@pytest.fixture
def client(vault_basic) -> TestClient:
    config = PublisherConfig(vault_path=vault_basic)
    app = create_app(config)
    return TestClient(app)


def test_root_returns_home(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "README" in response.text or "Welcome" in response.text
    assert 'src="/static/vaultpub/boot.js"' in response.text
    assert 'href="/static/vaultpub/common.css"' in response.text
    assert response.text.index("vaultpub/boot.js") < response.text.index("vaultpub/common.css") < response.text.index("vaultpub/app.css")


def test_root_renders_top_folder_navigation_toggle(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'data-nav-folder-layout="top"' in response.text
    assert 'data-vault-slides-url="/__slides-vault__"' in response.text
    assert 'id="vaultpub-slide-scopes"' in response.text
    assert '"label": "Whole vault"' in response.text
    assert 'title="Move folders to top bar"' in response.text


def test_scoped_notes_can_render_and_serve_vault_wide_attachments(tmp_path: Path) -> None:
    (tmp_path / "Published").mkdir()
    (tmp_path / "Elsewhere").mkdir()
    (tmp_path / "shared.png").write_bytes(b"png")
    (tmp_path / "Published" / "README.md").write_text(
        "![[shared.png]]\n\n![shared](shared.png)\n",
        encoding="utf-8",
    )
    (tmp_path / "Elsewhere" / "Private.md").write_text("# Private", encoding="utf-8")

    app = create_app(
        PublisherConfig(
            vault_path=tmp_path,
            include_folders=("Published",),
            include_all_attachments=True,
            realtime=False,
        )
    )
    client = TestClient(app)

    home = client.get("/")
    assert home.status_code == 200
    assert home.text.count('src="/__assets__/shared.png"') == 2
    assert "Elsewhere" not in home.text
    assert client.get("/__assets__/shared.png").status_code == 200
    assert client.get("/Elsewhere/Private.md").status_code == 404
    assert client.get("/__api__/search?q=Private").json() == {"results": []}


def test_note_page(client) -> None:
    response = client.get("/README.md")
    assert response.status_code == 200
    assert "README" in response.text
    assert 'data-sidebar-toggle="left"' in response.text
    assert 'data-sidebar-toggle="right"' in response.text
    assert 'data-nav-tree-action="expand"' in response.text
    assert 'data-nav-tree-action="collapse"' in response.text
    assert 'title="Expand all"' in response.text
    assert 'title="Collapse all"' in response.text
    assert 'data-nav-sort' in response.text
    assert "Page" in response.text
    assert 'class="topbar-context topbar-context-note"' in response.text
    assert 'data-layout-action="toggle-wide"' not in response.text
    assert 'data-slide-note-url="/__slides__/README.md"' in response.text
    assert 'data-vault-slides-url="/__slides-vault__"' in response.text
    assert 'data-current-heading' in response.text
    assert "Home" in response.text
    assert "README.md" in response.text


def test_live_order_editor_saves_only_navigation_metadata(tmp_path: Path) -> None:
    (tmp_path / "Folder").mkdir()
    (tmp_path / "Folder" / "README.md").write_text("# Folder", encoding="utf-8")
    (tmp_path / "A.md").write_text("# A", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B", encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    home = client.get("/")
    assert 'data-order-editor-url="/__settings__/order"' in home.text
    editor = client.get("/__settings__/order")
    assert editor.status_code == 200
    assert 'data-order-editor' in editor.text

    payload = client.get("/__api__/settings/order?directory=.").json()
    saved = client.post(
        "/__api__/settings/order",
        json={
            "action": "save",
            "directory": ".",
            "revision": payload["revision"],
            "folders": ["Folder/"],
            "files": ["B.md", "A.md"],
        },
    )
    assert saved.status_code == 200
    assert (tmp_path / "__order__.json").read_text(encoding="utf-8") == '[\n  "Folder/",\n  "B.md",\n  "A.md"\n]\n'
    assert (tmp_path / "A.md").read_text(encoding="utf-8") == "# A"

    reset = client.post(
        "/__api__/settings/order",
        json={
            "action": "reset",
            "directory": ".",
            "revision": saved.json()["revision"],
        },
    )
    assert reset.status_code == 200
    assert not (tmp_path / "__order__.json").exists()


def test_live_order_editor_rejects_cross_origin_writes(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Home", encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))
    response = client.post("/__api__/settings/order", headers={"Origin": "https://other.example"}, json={})
    assert response.status_code == 403


def test_former_special_roots_now_serve_vault_content(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Home", encoding="utf-8")
    for root_name in ("_slides", "_settings", "_slides-vault", "api", "assets"):
        (tmp_path / root_name).mkdir()
        (tmp_path / root_name / "Note.md").write_text(f"# {root_name}", encoding="utf-8")

    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    for root_name in ("_slides", "_settings", "_slides-vault", "api", "assets"):
        response = client.get(f"/{root_name}/Note.md")
        assert response.status_code == 200
        assert "vaultpub-slides" not in response.text
    assert client.get("/_slides-vault").status_code == 404
    assert client.get("/api/search").status_code == 404


def test_note_page_code_blocks_default_wrap_and_line_numbers(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# README\n\n```python\nprint('a')\nprint('b')\n```\n",
        encoding="utf-8",
    )

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    css_response = client.get("/static/vaultpub/common.css")
    assert css_response.status_code == 200
    assert "code-line-content" in css_response.text
    assert "grid-template-columns:3.2em minmax(0,1fr)" in css_response.text

    js_response = client.get("/static/vaultpub/app.js")
    assert js_response.status_code == 200
    assert "__vite__mapDeps" in js_response.text
    assert "code-line-content" in js_response.text


def test_note_page_renders_toc_in_right_sidebar(client) -> None:
    response = client.get("/A.md")
    assert response.status_code == 200
    assert '<aside class="sidebar-right">' in response.text
    assert "<h3>Contents</h3>" in response.text


def test_note_page_uses_local_graph_placeholder(client) -> None:
    response = client.get("/A.md")
    assert response.status_code == 200
    assert 'id="graph-container"' in response.text
    assert 'data-graph-note-id="note:' in response.text


def test_api_search(client) -> None:
    response = client.get("/__api__/search?q=README")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_search_index_json(client) -> None:
    response = client.get("/search-index.json")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(doc["title"] == "README.md" for doc in data)


def test_api_graph(client) -> None:
    response = client.get("/__api__/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


def test_note_page_omits_graph_when_local_graph_is_too_small(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# README\n\n[[A]]\n", encoding="utf-8")
    (tmp_path / "A.md").write_text("# A\n", encoding="utf-8")

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    response = client.get("/README.md")
    assert response.status_code == 200
    assert 'id="graph-container"' not in response.text


def test_graph_json(client) -> None:
    response = client.get("/graph.json")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


def test_frontend_static_assets(client) -> None:
    boot_response = client.get("/static/vaultpub/boot.js")
    assert boot_response.status_code == 200
    assert "javascript" in boot_response.headers["content-type"]
    assert "vaultpub.settings" in boot_response.text
    assert "vaultpub.sidebarState" in boot_response.text
    assert "vaultpub-top-folders-booting" in boot_response.text

    common_response = client.get("/static/vaultpub/common.css")
    assert common_response.status_code == 200
    assert "text/css" in common_response.headers["content-type"]
    assert ".file-tree" in common_response.text
    assert "list-style:none" in common_response.text
    assert "--bg-color" in common_response.text
    assert ".markdown-body" in common_response.text

    css_response = client.get("/static/vaultpub/app.css")
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "@media(max-width:1180px)" in css_response.text
    assert "--sidebar-left-width" in css_response.text
    assert ".sidebar-resizer" in css_response.text

    js_response = client.get("/static/vaultpub/app.js")
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "scrollIntoView" not in js_response.text
    assert "scrollTop" in js_response.text


def test_note_not_found(client) -> None:
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_folder_note(client) -> None:
    response = client.get("/Folder/B.md")
    assert response.status_code == 200
    assert "Note B" in response.text or "B" in response.text
    assert 'href="/Folder/" class="topbar-breadcrumb-link topbar-breadcrumb-segment"' in response.text
    assert 'href="/Folder/B.md" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in response.text


def test_standalone_slide_page_uses_reveal_without_article_chrome(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Title\n\nIntro\n\n## Second\n\n[[Target]]\n", encoding="utf-8")
    (tmp_path / "Target.md").write_text("# Target\n", encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    article = client.get("/README.md")
    response = client.get("/__slides__/README.md")

    assert article.status_code == 200
    assert 'data-slide-note-url="/__slides__/README.md"' in article.text
    assert response.status_code == 200
    assert '<div class="reveal"><div class="slides">' in response.text
    assert response.text.count('<section class="vaultpub-slide"') == 2
    assert 'class="top-bar"' not in response.text
    assert 'class="slides-return"' not in response.text
    assert 'reveal-themes/' not in response.text
    assert '<html lang="en" class="theme-light">' in response.text
    assert '<body class="vaultpub-slides"' in response.text
    assert 'href="/Target.md"' in response.text


def test_standalone_slide_settings_honor_frontmatter_cookie_and_query_override(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "---\nslide:\n  split: single\n  codeWrap: false\n---\n\n# Title\n\n## Second\n",
        encoding="utf-8",
    )
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    default = client.get("/__slides__/README.md")
    cookie = client.get("/__slides__/README.md", cookies={"vaultpub_slide_split": "sections"})
    query = client.get("/__slides__/README.md?split=single", cookies={"vaultpub_slide_split": "sections"})

    assert default.text.count('<section class="vaultpub-slide"') == 1
    assert cookie.text.count('<section class="vaultpub-slide"') == 2
    assert query.text.count('<section class="vaultpub-slide"') == 1
    assert '"codeWrap": false' in default.text
    assert 'data-slide-layout="single"' in default.text
    assert 'data-slide-layout="single"' not in cookie.text
    assert 'data-slide-layout="single"' in query.text
    assert default.headers["vary"] == "Cookie"
    assert 'slides-boot.js' in default.text
    assert default.text.index("vaultpub/common.css") < default.text.index("vaultpub/slides.css")


def test_standalone_folder_slides_follow_navigation_order(tmp_path: Path) -> None:
    (tmp_path / "Course" / "Nested").mkdir(parents=True)
    (tmp_path / "Course" / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "Course" / "Nested" / "B.md").write_text("# B\n\n## Detail\n", encoding="utf-8")
    (tmp_path / "Course" / "__order__.json").write_text('["Nested/", "A.md"]', encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    directory = client.get("/Course/")
    response = client.get("/__slides-folder__/Course/")

    assert directory.status_code == 200
    assert 'data-slide-folder-url=' not in directory.text
    assert response.status_code == 200
    assert response.text.count("class=\"vaultpub-note-slot\"") == 2
    assert response.text.count('data-slide-kind="note-divider"') == 2
    assert response.text.find("Course/Nested/B.md") < response.text.find("Course/A.md")
    assert 'data-return-url="/Course/"' in response.text


def test_standalone_slide_routes_reject_private_non_markdown_and_empty_directories(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# README\n", encoding="utf-8")
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "Secret.md").write_text("# Secret\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not Markdown\n", encoding="utf-8")
    (tmp_path / "Empty").mkdir()
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    assert client.get("/__slides__/private/Secret.md").status_code == 404
    assert client.get("/__slides__/notes.txt").status_code == 404
    assert client.get("/__slides-folder__/Empty/").status_code == 404


def test_standalone_whole_vault_slides_follow_navigation_order_and_exclusions(tmp_path: Path) -> None:
    (tmp_path / "Course" / "Nested").mkdir(parents=True)
    (tmp_path / "private").mkdir()
    (tmp_path / "README.md").write_text("# README\n", encoding="utf-8")
    (tmp_path / "Course" / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "Course" / "Nested" / "B.md").write_text("# B\n\n## Detail\n", encoding="utf-8")
    (tmp_path / "private" / "Secret.md").write_text("# Secret\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not Markdown\n", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["Course/", "README.md"]', encoding="utf-8")
    (tmp_path / "Course" / "__order__.json").write_text('["Nested/", "A.md"]', encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    response = client.get("/__slides-vault__")

    assert response.status_code == 200
    assert response.text.count("class=\"vaultpub-note-slot\"") == 3
    assert response.text.count('data-slide-kind="note-divider"') == 3
    assert response.text.find("Course/Nested/B.md") < response.text.find("Course/A.md") < response.text.find("README.md")
    assert "Secret.md" not in response.text
    assert 'data-return-url="/"' in response.text
    assert '"transition": "slide"' in response.text


def test_standalone_whole_vault_slides_reject_empty_vault(tmp_path: Path) -> None:
    (tmp_path / "Empty").mkdir()
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    assert client.get("/__slides-vault__").status_code == 404


def test_standalone_multi_note_slides_validate_sort_and_scope_payload(tmp_path: Path) -> None:
    (tmp_path / "Course").mkdir()
    (tmp_path / "Empty").mkdir()
    (tmp_path / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "Z.md").write_text("# Z\n", encoding="utf-8")
    (tmp_path / "Course" / "B.md").write_text("# B\n", encoding="utf-8")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    page = client.get("/A.md")
    descending = client.get("/__slides-vault__?sort=name-desc&split=single")
    fallback = client.get("/__slides-vault__?sort=invalid&split=single")

    assert '"label": "Course/"' in page.text
    assert "Empty/" not in page.text
    assert descending.text.find("Course/B.md") < descending.text.find("Z.md") < descending.text.find("A.md")
    assert fallback.text.find("Course/B.md") < fallback.text.find("A.md") < fallback.text.find("Z.md")
    assert descending.text.count('data-slide-kind="note-divider"') == 3
    assert 'data-vaultpub-multi-note="true"' in descending.text
    assert 'vaultpub-slide-manifest' in descending.text
    assert 'slides-print-notice' in client.get("/__slides-vault__?print-pdf").text


def test_standalone_multi_note_slide_payload_is_rendered_per_note_and_defers_media(tmp_path: Path) -> None:
    (tmp_path / "A.md").write_text("# A\n\nA-only-body\n", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B\n\n![[image.png]]\n\nB-only-body\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"png")
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    deck = client.get("/__slides-vault__")
    payload = client.get("/__api__/slides/B.md")

    assert deck.status_code == 200
    assert "A-only-body" not in deck.text
    assert "B-only-body" not in deck.text
    assert payload.status_code == 200
    assert payload.headers["cache-control"] == "no-store"
    assert payload.headers["vary"] == "Cookie"
    data = payload.json()
    assert data["sourcePath"] == "B.md"
    assert "B-only-body" in data["slides"][0]["html"]
    assert 'data-vaultpub-src="/__assets__/image.png"' in data["slides"][0]["html"]
    assert client.get("/__api__/slides/missing.md").status_code == 404


def test_api_page(client) -> None:
    response = client.get("/__api__/page/README.md")
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "title" in data


def test_directory_page(client) -> None:
    response = client.get("/Folder/")
    assert response.status_code == 200
    assert 'class="directory-page"' in response.text
    assert 'class="directory-list"' in response.text
    assert 'class="sidebar-title">Directory<' in response.text
    assert 'class="directory-context-nav"' in response.text
    assert 'href="/A.md"' in response.text
    assert 'href="/README.md"' in response.text
    assert "Same Directory" in response.text
    assert 'href="/Folder/B.md"' in response.text
    assert 'href="/Folder/" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in response.text
    assert 'class="directory-list-item is-file"' in response.text
    assert 'directory-list-title">B.md<' in response.text
    assert 'directory-list-preview"># Note B' in response.text
    assert "This is note B in a folder." in response.text
    assert 'directory-list-meta">Folder/B.md<' not in response.text


def test_navigation_json_controls_are_not_published_and_shape_directory_page(tmp_path: Path) -> None:
    (tmp_path / "Guides").mkdir()
    (tmp_path / "README.md").write_text("# README", encoding="utf-8")
    (tmp_path / "A.md").write_text("# A", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B", encoding="utf-8")
    (tmp_path / "Guides" / "Inside.md").write_text("# Inside", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["B.md", "Guides/"]', encoding="utf-8")
    (tmp_path / "__star__.json").write_text('["README.md"]', encoding="utf-8")
    (tmp_path / "Guides" / "__category__.json").write_text(
        '{"title": "Documentation", "description": "Read this first", "icon": "📘"}',
        encoding="utf-8",
    )
    client = TestClient(create_app(PublisherConfig(vault_path=tmp_path, realtime=False)))

    root = client.get("/")
    directory = client.get("/Guides/")

    assert root.status_code == 200
    assert 'data-nav-sort' in root.text
    assert '<option value="modified-desc" selected>Modified newest</option>' in root.text
    assert 'data-nav-starred="true"' in root.text
    assert 'data-nav-predefined-order="true"' in root.text
    assert root.text.index("README.md") < root.text.index("B.md") < root.text.index("Documentation/")
    assert "__order__.json" not in root.text
    assert client.get("/__order__.json").status_code == 404
    assert directory.status_code == 200
    assert "Documentation/" in directory.text
    assert "Read this first" in directory.text


def test_old_extensionless_note_route_is_not_supported(client) -> None:
    response = client.get("/Folder/B")
    assert response.status_code == 404


def test_force_included_text_page_renders_topbar_code_tools(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# README\n", encoding="utf-8")
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "example.py").write_text("print('hello')\n", encoding="utf-8")

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False, force_include_regexes=(r".*\.py$",)))
    client = TestClient(app)

    response = client.get("/tools/example.py")
    assert response.status_code == 200
    assert 'class="topbar-context topbar-context-code"' in response.text
    assert 'data-layout-action="toggle-wide"' not in response.text
    assert 'data-vault-slides-url="/__slides-vault__"' in response.text
    assert 'href="/tools/" class="topbar-breadcrumb-link topbar-breadcrumb-segment"' in response.text
    assert 'href="/tools/example.py" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in response.text
    assert 'data-code-action="copy-path"' in response.text
    assert 'data-code-action="toggle-wrap"' in response.text
    assert "tools/example.py" in response.text


def test_local_resource_links_render_and_serve(vault_local_resources) -> None:
    app = create_app(
        PublisherConfig(
            vault_path=vault_local_resources,
            realtime=False,
            force_include_regexes=(r".*\.py$",),
        )
    )
    client = TestClient(app)

    page = client.get("/subdir/README.md")
    assert page.status_code == 200
    assert 'src="/__assets__/subdir/image.png"' in page.text
    assert 'href="/__assets__/subdir/doc.pdf"' in page.text
    assert '<a href="/__assets__/subdir/archive.pin.gz" download="archive.pin.gz">Archive Download</a>' in page.text
    assert '<a href="/__assets__/subdir/archive.pin.gz" download="archive.pin.gz">Archive Link</a>' in page.text
    assert 'href="/subdir/tool.py"' in page.text
    assert 'href="/subdir/Other.md"' in page.text
    assert 'href="./missing.gz"' in page.text
    assert 'href="./missing.txt"' in page.text

    asset = client.get("/__assets__/subdir/image.png")
    assert asset.status_code == 200
    assert "image/png" in asset.headers["content-type"]

    archive = client.get("/__assets__/subdir/archive.pin.gz")
    assert archive.status_code == 200
    assert "application/gzip" in archive.headers["content-type"]
    assert archive.headers["content-disposition"] == 'attachment; filename="archive.pin.gz"'

    text_page = client.get("/subdir/tool.py")
    assert text_page.status_code == 200
    assert 'class="topbar-context topbar-context-code"' in text_page.text
    assert "embedded tool" in text_page.text


def test_local_resource_links_decode_percent_escapes_and_fallback_parent_segments(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "Exported image 20260608223536-1.png").write_text("fake image", encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text(
        (
            "# Home\n\n"
            "![Image](../../../../../attachments/Exported%20image%2020260608223536-1.png)\n"
        ),
        encoding="utf-8",
    )

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    page = client.get("/general/README.md")
    assert page.status_code == 200
    assert '/__assets__/attachments/Exported image 20260608223536-1.png' in page.text

    asset = client.get("/__assets__/attachments/Exported%20image%2020260608223536-1.png")
    assert asset.status_code == 200
    assert asset.headers["content-type"].startswith("image/png")


def test_obsidian_dynamic_text_file_embed_renders_and_serves_asset(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "config.toml").write_text('name = "vaultpub"\n', encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text("![[../attachments/config.toml]]\n", encoding="utf-8")

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    asset_before = client.get("/__assets__/attachments/config.toml")
    assert asset_before.status_code == 404

    page = client.get("/general/README.md")
    assert page.status_code == 200
    assert 'data-embed-source="/__assets__/attachments/config.toml"' in page.text
    assert 'class="text-page-embed-tools"' in page.text
    assert 'class="topbar-code-btn"' in page.text
    assert 'data-code-action="toggle-wrap"' in page.text
    assert 'class="language-toml"' in page.text

    asset_after = client.get("/__assets__/attachments/config.toml")
    assert asset_after.status_code == 200
    assert asset_after.text == 'name = "vaultpub"\n'


def test_permalink_and_alias_routes_and_api(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "---\npermalink: about\naliases:\n  - Old Home\n---\n# Home\n",
        encoding="utf-8",
    )
    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    default_response = client.get("/README.md")
    assert default_response.status_code == 200

    canonical_response = client.get("/about")
    assert canonical_response.status_code == 404

    alias_response = client.get("/Old%20Home")
    assert alias_response.status_code == 404

    api_response = client.get("/__api__/page/README.md")
    assert api_response.status_code == 200
    assert api_response.json()["url"] == "/README.md"


def test_realtime_shutdown_signals_watcher_stop(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("# README\n", encoding="utf-8")
    stop_seen = threading.Event()

    async def fake_watch_vault(config, indexer, bus, state, debounce_ms=150, stop_event=None, rust_timeout_ms=250):
        assert stop_event is not None
        try:
            while not stop_event.is_set():
                await asyncio.sleep(0.01)
        finally:
            if stop_event.is_set():
                stop_seen.set()

    monkeypatch.setattr("vaultpub.web.app.watch_vault", fake_watch_vault)

    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=True))
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

    assert stop_seen.wait(1.0)
