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


@override_settings(ROOT_URLCONF=__name__)
def test_django_page_uses_packaged_template(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/")

    assert response.status_code == 200
    assert b'class="top-bar"' in response.content
    assert b'class="markdown-body"' in response.content
    assert b"README" in response.content
    assert b'data-url-prefix="/notes/"' in response.content
    assert b'href="/notes/README"' in response.content
    assert b'href="/README"' not in response.content
    assert b"{% toc %}" not in response.content


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

    page = client.get("/notes/api/page/README")
    assert page.status_code == 200
    page_data = page.json()
    assert page_data["url"] == "/notes/README"
    assert 'href="/notes/A"' in page_data["html"]

    search = client.get("/notes/api/search?q=README")
    assert search.status_code == 200
    assert search.json()["results"][0]["url"].startswith("/notes/")

    graph = client.get("/notes/api/graph")
    assert graph.status_code == 200
    note_urls = [node["url"] for node in graph.json()["nodes"] if node["group"] == "note"]
    assert note_urls
    assert all(url.startswith("/notes/") for url in note_urls)
