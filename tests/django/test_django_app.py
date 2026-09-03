"""Tests for Django integration."""
from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client, RequestFactory, override_settings
from django.urls import include, path

import django
from vaultpub.core.config import PublisherConfig
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
            SECRET_KEY="test-secret-key",
            ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
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
    assert b'data-slide-note-url="/notes/_slides/README.md"' in response.content
    assert b'data-vault-slides-url="/notes/_slides-vault"' in response.content
    assert b'id="vaultpub-slide-scopes"' in response.content
    assert b'"label": "Whole vault"' in response.content
    assert b'topbar-present-action' not in response.content
    assert b'data-nav-folder-layout="top"' in response.content
    assert b'title="Move folders to top bar"' in response.content
    assert b'data-current-heading' in response.content
    assert b'class="markdown-body"' in response.content
    assert b"README" in response.content
    assert b'data-url-prefix="/notes/"' in response.content
    assert b'src="/static/vaultpub/boot.js"' in response.content
    assert b'href="/static/vaultpub/common.css"' in response.content
    assert response.content.index(b"vaultpub/boot.js") < response.content.index(b"vaultpub/common.css") < response.content.index(b"vaultpub/app.css")
    assert b'href="/notes/"' in response.content
    assert b"README.md" in response.content
    assert b'class="slides-return"' not in response.content
    assert b'href="/README.md"' not in response.content
    assert b"{% toc %}" not in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_page_uses_local_graph_placeholder(django_setup) -> None:
    views._state_cache.clear()
    response = Client().get("/notes/A.md")

    assert response.status_code == 200
    assert b'id="graph-container"' in response.content
    assert b'data-graph-note-id="note:' in response.content
    assert response.content.count(b"<h3>Contents</h3>") == 1


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
def test_django_slide_page_uses_dedicated_layout_and_mount_prefix(django_setup, tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "figure.png").write_bytes(b"image")
    (tmp_path / "README.md").write_text(
        "---\nslide:\n  theme: dracula\n  transition: fade\n---\n\n# Title\n\nIntro\n\n## Second\n\n![[images/figure.png]]\n",
        encoding="utf-8",
    )

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={"default": {"vault_path": str(tmp_path), "url_prefix": "/notes/", "realtime": False}}
    ):
        client = Client()
        article = client.get("/notes/README.md")
        response = client.get("/notes/_slides/README.md")
        single = client.get("/notes/_slides/README.md?split=single")

    assert article.status_code == 200
    assert b'data-slide-note-url="/notes/_slides/README.md"' in article.content
    assert response.status_code == 200
    assert b'<div class="reveal"><div class="slides">' in response.content
    assert response.content.count(b'<section class="vaultpub-slide"') == 2
    assert b'class="top-bar"' not in response.content
    assert b'data-return-url="/notes/README.md"' in response.content
    assert b'src="/notes/assets/images/figure.png"' in response.content
    assert b'<html lang="en" class="theme-dracula">' in response.content
    assert b'<body class="vaultpub-slides"' in response.content
    assert b'reveal-themes/' not in response.content
    assert b'"transition": "fade"' in response.content
    assert b'vaultpub-slide-settings' in response.content
    assert b'data-slide-layout="single"' not in response.content
    assert b'data-slide-layout="single"' in single.content
    assert b'slides-boot.js' in response.content
    assert response.content.index(b"vaultpub/common.css") < response.content.index(b"vaultpub/slides.css")
    assert response.headers["Vary"] == "Cookie"


@override_settings(ROOT_URLCONF=__name__)
def test_django_folder_slides_are_recursive_and_reject_missing_or_private_notes(django_setup, tmp_path: Path) -> None:
    (tmp_path / "Course" / "Nested").mkdir(parents=True)
    (tmp_path / "private").mkdir()
    (tmp_path / "Course" / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "Course" / "Nested" / "B.md").write_text("# B\n\n## Detail\n", encoding="utf-8")
    (tmp_path / "private" / "Secret.md").write_text("# Secret\n", encoding="utf-8")
    (tmp_path / "Course" / "__order__.json").write_text('["Nested/", "A.md"]', encoding="utf-8")

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={"default": {"vault_path": str(tmp_path), "url_prefix": "/notes/", "realtime": False}}
    ):
        client = Client()
        directory = client.get("/notes/Course/")
        response = client.get("/notes/_slides-folder/Course/")
        missing = client.get("/notes/_slides/missing.md")
        private = client.get("/notes/_slides/private/Secret.md")

    assert directory.status_code == 200
    assert b'data-slide-folder-url=' not in directory.content
    assert response.status_code == 200
    assert response.content.count(b'class="vaultpub-note-slot"') == 2
    assert response.content.count(b'data-slide-kind="note-divider"') == 2
    assert response.content.find(b"Course/Nested/B.md") < response.content.find(b"Course/A.md")
    assert b'data-return-url="/notes/Course/"' in response.content
    assert missing.status_code == 404
    assert private.status_code == 404


@override_settings(ROOT_URLCONF=__name__)
def test_django_whole_vault_slides_follow_navigation_order_and_mount_prefix(django_setup, tmp_path: Path) -> None:
    (tmp_path / "Course" / "Nested").mkdir(parents=True)
    (tmp_path / "private").mkdir()
    (tmp_path / "README.md").write_text("# README\n", encoding="utf-8")
    (tmp_path / "Course" / "A.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "Course" / "Nested" / "B.md").write_text("# B\n\n## Detail\n", encoding="utf-8")
    (tmp_path / "private" / "Secret.md").write_text("# Secret\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not Markdown\n", encoding="utf-8")
    (tmp_path / "__order__.json").write_text('["Course/", "README.md"]', encoding="utf-8")
    (tmp_path / "Course" / "__order__.json").write_text('["Nested/", "A.md"]', encoding="utf-8")

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={"default": {"vault_path": str(tmp_path), "url_prefix": "/notes/", "realtime": False}}
    ):
        response = Client().get("/notes/_slides-vault")

    assert response.status_code == 200
    assert response.content.count(b'class="vaultpub-note-slot"') == 3
    assert response.content.count(b'data-slide-kind="note-divider"') == 3
    assert response.content.find(b"Course/Nested/B.md") < response.content.find(b"Course/A.md") < response.content.find(b"README.md")
    assert b"Secret.md" not in response.content
    assert b'data-return-url="/notes/"' in response.content
    assert b'"transition": "slide"' in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_django_multi_note_slide_payload_uses_mount_prefix_and_defers_media(django_setup, tmp_path: Path) -> None:
    (tmp_path / "A.md").write_text("# A\n\nA-only-body\n", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B\n\n![[image.png]]\n\nB-only-body\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"png")

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={"default": {"vault_path": str(tmp_path), "url_prefix": "/notes/", "realtime": False}}
    ):
        client = Client()
        deck = client.get("/notes/_slides-vault")
        payload = client.get("/notes/api/slides/B.md")

    assert deck.status_code == 200
    assert b"A-only-body" not in deck.content
    assert b"B-only-body" not in deck.content
    assert b'"payloadUrl": "/notes/api/slides/B.md"' in deck.content
    assert payload.status_code == 200
    assert payload.headers["Cache-Control"] == "no-store"
    assert payload.headers["Vary"] == "Cookie"
    data = payload.json()
    assert b"B-only-body" in payload.content
    assert 'data-vaultpub-src="/notes/assets/image.png"' in data["slides"][0]["html"]


@override_settings(ROOT_URLCONF=__name__)
def test_django_whole_vault_slides_reject_empty_vault(django_setup, tmp_path: Path) -> None:
    (tmp_path / "Empty").mkdir()

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={"default": {"vault_path": str(tmp_path), "url_prefix": "/notes/", "realtime": False}}
    ):
        response = Client().get("/notes/_slides-vault")

    assert response.status_code == 404


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


@override_settings(ROOT_URLCONF=__name__)
def test_django_mount_prefixes_dynamic_text_file_embed(django_setup, tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "general").mkdir()
    (tmp_path / "attachments" / "config.toml").write_text('name = "vaultpub"\n', encoding="utf-8")
    (tmp_path / "general" / "README.md").write_text("![[../attachments/config.toml]]\n", encoding="utf-8")

    views._state_cache.clear()
    with override_settings(
        VAULTPUB={
            "default": {
                "vault_path": str(tmp_path),
                "url_prefix": "/notes/",
                "home_file": "README",
                "show_graph": True,
                "show_backlinks": True,
                "show_search": True,
            }
        }
    ):
        client = Client()
        asset_before = client.get("/notes/assets/attachments/config.toml")
        page = client.get("/notes/general/README.md")
        asset_after = client.get("/notes/assets/attachments/config.toml")

    assert asset_before.status_code == 404
    assert page.status_code == 200
    assert b'href="/notes/assets/attachments/config.toml"' in page.content
    assert b'class="text-page-embed-tools"' in page.content
    assert b'class="topbar-code-btn"' in page.content
    assert b'data-code-action="toggle-wrap"' in page.content
    assert b'class="language-toml"' in page.content
    assert asset_after.status_code == 200
    assert b"".join(asset_after.streaming_content) == b'name = "vaultpub"\n'


@override_settings(ROOT_URLCONF=__name__)
def test_dynamic_config_render_helpers_use_supplied_prefix(django_setup) -> None:
    views._state_cache.clear()
    request = RequestFactory().get("/custom/README.md")
    config = PublisherConfig(
        vault_path=FIXTURES_DIR / "vault_basic",
        url_prefix="/custom/",
        home_file="README",
        realtime=False,
    )

    response = views.render_page_with_config(
        request,
        config,
        "README.md",
        cache_key="test-dynamic-prefix",
        force_refresh=True,
    )

    assert response.status_code == 200
    assert b'data-url-prefix="/custom/"' in response.content
    assert b'href="/custom/A.md"' in response.content


@override_settings(ROOT_URLCONF=__name__)
def test_dynamic_config_attachment_streams_file_response(django_setup, vault_local_resources) -> None:
    views._state_cache.clear()
    request = RequestFactory().get("/custom/assets/subdir/archive.pin.gz")
    config = PublisherConfig(
        vault_path=vault_local_resources,
        url_prefix="/custom/",
        home_file="README",
        realtime=False,
    )

    response = views.render_attachment_with_config(
        request,
        config,
        "subdir/archive.pin.gz",
        cache_key="test-dynamic-attachment",
        force_refresh=True,
    )

    assert response.status_code == 200
    assert response.streaming
    assert response["Content-Disposition"] == 'attachment; filename="archive.pin.gz"'
