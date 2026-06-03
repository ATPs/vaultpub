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
    response = client.get("/README")
    assert response.status_code == 200
    assert "README" in response.text


def test_api_search(client) -> None:
    response = client.get("/api/search?q=README")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_api_graph(client) -> None:
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


def test_note_not_found(client) -> None:
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_folder_note(client) -> None:
    response = client.get("/Folder/B")
    assert response.status_code == 200
    assert "Note B" in response.text or "B" in response.text


def test_api_page(client) -> None:
    response = client.get("/api/page/README")
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "title" in data


def test_permalink_and_alias_routes_and_api(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "---\npermalink: about\naliases:\n  - Old Home\n---\n# Home\n",
        encoding="utf-8",
    )
    app = create_app(PublisherConfig(vault_path=tmp_path, realtime=False))
    client = TestClient(app)

    default_response = client.get("/README", follow_redirects=False)
    assert default_response.status_code == 301
    assert default_response.headers["location"] == "/about"

    canonical_response = client.get("/about")
    assert canonical_response.status_code == 200
    assert "Home" in canonical_response.text

    alias_response = client.get("/Old%20Home", follow_redirects=False)
    assert alias_response.status_code == 301
    assert alias_response.headers["location"] == "/about"

    api_response = client.get("/api/page/about")
    assert api_response.status_code == 200
    assert api_response.json()["url"] == "/about"
