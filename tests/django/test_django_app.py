"""Tests for Django integration."""
from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings

import django

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


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
