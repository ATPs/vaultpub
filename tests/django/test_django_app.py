"""Tests for Django integration."""
from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client, override_settings
from django.urls import include, path

import django
from vaultpub.django_app import views

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

urlpatterns = [
    path("notes/", include("vaultpub.django_app.urls")),
]


@pytest.fixture(scope="module")
def django_setup() -> None:
    vault_basic = FIXTURES_DIR / "vault_basic"
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            INSTALLED_APPS=[
                "django.contrib.staticfiles",
                "vaultpub.django_app",
            ],
            ROOT_URLCONF=[],
            VAULTPUB={
                "default": {
                    "vault_path": str(vault_basic),
                    "url_prefix": "/notes/",
                    "home_file": "README",
                    "show_graph": True,
                    "show_backlinks": True,
                    "show_search": True,
                }
            },
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {"context_processors": []},
                }
            ],
            STATIC_URL="/static/",
        )
        django.setup()


def test_app_config_loads(django_setup) -> None:
    from vaultpub.django_app.apps import VaultpubConfig
    assert VaultpubConfig.name == "vaultpub.django_app"


def test_conf_parses(django_setup) -> None:
    from vaultpub.django_app.conf import get_default_config
    config = get_default_config()
    assert config is not None
    assert config.url_prefix == "/notes/"
    assert config.home_file == "README"
    assert "gz" in config.allowed_attachment_types


@override_settings(
    VAULTPUB={
        "default": {
            "vault_path": str(FIXTURES_DIR / "vault_basic"),
            "url_prefix": "/notes/",
            "allowed_attachment_types": ["pdf", "gz"],
        }
    }
)
def test_conf_reads_allowed_attachment_types_from_settings(django_setup) -> None:
    from vaultpub.django_app.conf import get_default_config

    views._state_cache.clear()
    config = get_default_config()

    assert config is not None
    assert config.allowed_attachment_types == ("pdf", "gz")


@override_settings(ROOT_URLCONF=__name__)
def test_django_page_uses_packaged_template(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/")

    assert response.status_code == 200
    assert b'class="top-bar"' in response.content
    assert b'class="topbar-context topbar-context-note"' in response.content
    assert b'data-current-heading' in response.content
    assert b'class="markdown-body"' in response.content
    assert b"README" in response.content
    assert b'data-url-prefix="/notes/"' in response.content
    assert b'href="/notes/"' in response.content
    assert b"README.md" in response.content
    assert b'href="/notes/README.md"' in response.content
    assert b'href="/README.md"' not in response.content
    assert b"{% toc %}" not in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_page_uses_local_graph_placeholder(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/A.md")

    assert response.status_code == 200
    assert b'id="graph-container"' in response.content
    assert b'data-graph-note-id="note:' in response.content


@override_settings(
    ROOT_URLCONF=__name__,
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [],
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {
                            "vaultpub/base.html": (
                                "<html><body>OVERRIDDEN {{ site_name }}"
                                "{% block content %}{% endblock %}</body></html>"
                            ),
                        },
                    ),
                    "django.template.loaders.app_directories.Loader",
                ],
            },
        }
    ],
)
def test_django_template_override_changes_layout(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/")

    assert response.status_code == 200
    assert b"OVERRIDDEN vaultpub" in response.content
    assert b'class="markdown-body"' in response.content
    assert b'class="top-bar"' not in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_api_urls_include_mount_prefix(django_setup) -> None:
    views._state_cache.clear()
    client = Client()

    page = client.get("/notes/api/page/README.md")
    assert page.status_code == 200
    page_data = page.json()
    assert page_data["url"] == "/notes/README.md"
    assert 'href="/notes/A.md"' in page_data["html"]

    search = client.get("/notes/api/search?q=README")
    assert search.status_code == 200
    assert search.json()["results"][0]["url"].startswith("/notes/")

    graph = client.get("/notes/api/graph")
    assert graph.status_code == 200
    note_urls = [node["url"] for node in graph.json()["nodes"] if node["group"] == "note"]
    assert note_urls
    assert all(url.startswith("/notes/") for url in note_urls)


@override_settings(ROOT_URLCONF=__name__)
def test_django_page_omits_graph_when_local_graph_is_too_small(django_setup, tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# README\n\n[[A]]\n", encoding="utf-8")
    (tmp_path / "A.md").write_text("# A\n", encoding="utf-8")

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={
            "default": {
                "vault_path": str(tmp_path),
                "url_prefix": "/notes/",
                "home_file": "README",
                "show_graph": True,
                "show_search": True,
            }
        }
    ):
        response = Client().get("/notes/README.md")

    assert response.status_code == 200
    assert b'id="graph-container"' not in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_directory_page(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/Folder/")

    assert response.status_code == 200
    assert b'class="directory-page"' in response.content
    assert b'class="directory-list"' in response.content
    assert b'class="sidebar-title">Directory<' in response.content
    assert b'data-nav-tree-action="expand"' in response.content
    assert b'data-nav-tree-action="collapse"' in response.content
    assert b'title="Expand all"' in response.content
    assert b'title="Collapse all"' in response.content
    assert b'class="directory-context-nav"' in response.content
    assert b'href="/notes/A.md"' in response.content
    assert b'href="/notes/README.md"' in response.content
    assert b"Same Directory" in response.content
    assert b'href="/notes/Folder/B.md"' in response.content
    assert b'href="/notes/Folder/" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in response.content
    assert b'class="directory-list-item is-file"' in response.content
    assert b'directory-list-preview"># Note B' in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_nested_note_breadcrumb_links_use_mount_prefix(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/Folder/B.md")

    assert response.status_code == 200
    assert b'href="/notes/Folder/" class="topbar-breadcrumb-link topbar-breadcrumb-segment"' in response.content
    assert b'href="/notes/Folder/B.md" class="topbar-breadcrumb-link topbar-breadcrumb-current"' in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_mount_prefixes_local_resource_urls(django_setup, vault_local_resources) -> None:
    views._state_cache.clear()
    with override_settings(
        VAULTPUB={
            "default": {
                "vault_path": str(vault_local_resources),
                "url_prefix": "/notes/",
                "home_file": "README",
                "show_graph": True,
                "show_backlinks": True,
                "show_search": True,
                "force_include_regexes": [r".*\.py$"],
            }
        }
    ):
        client = Client()
        page = client.get("/notes/subdir/README.md")
        asset = client.get("/notes/assets/subdir/image.png")
        archive = client.get("/notes/assets/subdir/archive.pin.gz")
        text_page = client.get("/notes/subdir/tool.py")

    assert page.status_code == 200
    assert b'src="/notes/assets/subdir/image.png"' in page.content
    assert b'href="/notes/assets/subdir/doc.pdf"' in page.content
    assert b'href="/notes/assets/subdir/archive.pin.gz" download="archive.pin.gz"' in page.content
    assert b'href="/notes/subdir/tool.py"' in page.content
    assert b'href="/notes/subdir/Other.md"' in page.content
    assert asset.status_code == 200
    assert asset["content-type"].startswith("image/png")
    assert archive.status_code == 200
    assert archive["content-type"].startswith("application/gzip")
    assert archive["Content-Disposition"] == 'attachment; filename="archive.pin.gz"'
    assert text_page.status_code == 200
    assert b'class="topbar-context topbar-context-code"' in text_page.content
