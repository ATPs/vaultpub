"""Django URL configuration for vaultpub."""
from __future__ import annotations

from django.urls import path

from vaultpub.django_app import views

app_name = "vaultpub"

urlpatterns = [
    path("", views.index, name="home"),
    path("assets/<path:asset_path>", views.attachment, name="attachment"),
    path("api/page/<path:note_path>", views.api_page, name="api_page"),
    path("api/search", views.api_search, name="api_search"),
    path("api/graph", views.api_graph, name="api_graph"),
    path("api/graph/local/<path:note_path>", views.api_local_graph, name="api_local_graph"),
    path("_slides-vault", views.slides_vault, name="slides_vault"),
    path("_slides-folder/<path:directory_path>", views.slides_folder, name="slides_folder"),
    path("_slides/<path:note_path>", views.slides, name="slides"),
    path("<path:note_path>", views.page, name="page"),
]
