"""Integration tests for the ASGI web app."""
from __future__ import annotations

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


def test_note_page(client) -> None:
    response = client.get("/README.md")
    assert response.status_code == 200
    assert "README" in response.text
    assert 'data-sidebar-toggle="left"' in response.text
    assert 'data-sidebar-toggle="right"' in response.text
    assert "Navigation" in response.text
    assert "Page" in response.text
    assert 'class="topbar-context topbar-context-note"' in response.text
    assert 'data-current-heading' in response.text
    assert "Home" in response.text
    assert "README.md" in response.text


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
    response = client.get("/api/search?q=README")
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
    response = client.get("/api/graph")
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
    css_response = client.get("/static/vaultpub/app.css")
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]

    js_response = client.get("/static/vaultpub/app.js")
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]


def test_note_not_found(client) -> None:
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_folder_note(client) -> None:
    response = client.get("/Folder/B.md")
    assert response.status_code == 200
    assert "Note B" in response.text or "B" in response.text


def test_api_page(client) -> None:
    response = client.get("/api/page/README.md")
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "title" in data


def test_directory_page(client) -> None:
    response = client.get("/Folder/")
    assert response.status_code == 200
    assert 'class="directory-page"' in response.text
    assert 'href="/Folder/B.md"' in response.text


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
    assert 'data-code-action="copy-path"' in response.text
    assert 'data-code-action="toggle-wrap"' in response.text
    assert "tools/example.py" in response.text


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

    api_response = client.get("/api/page/README.md")
    assert api_response.status_code == 200
    assert api_response.json()["url"] == "/README.md"
