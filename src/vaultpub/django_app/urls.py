"""Django URL configuration for vaultpub."""
from __future__ import annotations

from django.urls import path

from vaultpub.core.paths import (
    API_URL_PREFIX,
    ASSET_URL_PREFIX,
    SETTINGS_URL_PREFIX,
    SLIDES_FOLDER_URL_PREFIX,
    SLIDES_URL_PREFIX,
    SLIDES_VAULT_URL,
)
from vaultpub.django_app import views

app_name = "vaultpub"

urlpatterns = [
    path("", views.index, name="home"),
    path(f"{ASSET_URL_PREFIX.lstrip('/')}/<path:asset_path>", views.attachment, name="attachment"),
    path(f"{API_URL_PREFIX.lstrip('/')}/page/<path:note_path>", views.api_page, name="api_page"),
    path(f"{API_URL_PREFIX.lstrip('/')}/slides/<path:note_path>", views.api_slides, name="api_slides"),
    path(f"{API_URL_PREFIX.lstrip('/')}/search", views.api_search, name="api_search"),
    path(f"{API_URL_PREFIX.lstrip('/')}/graph", views.api_graph, name="api_graph"),
    path(f"{API_URL_PREFIX.lstrip('/')}/graph/local/<path:note_path>", views.api_local_graph, name="api_local_graph"),
    path(f"{API_URL_PREFIX.lstrip('/')}/settings/order", views.api_order_editor, name="api_order_editor"),
    path(SLIDES_VAULT_URL.lstrip("/"), views.slides_vault, name="slides_vault"),
    path(f"{SLIDES_FOLDER_URL_PREFIX.lstrip('/')}/<path:directory_path>", views.slides_folder, name="slides_folder"),
    path(f"{SLIDES_URL_PREFIX.lstrip('/')}/<path:note_path>", views.slides, name="slides"),
    path(f"{SETTINGS_URL_PREFIX.lstrip('/')}/order", views.order_editor, name="order_editor"),
    path("<path:note_path>", views.page, name="page"),
]
