from __future__ import annotations

import json

import pytest

from vaultpub.core.config import PublisherConfig
from vaultpub.core.index.indexer import VaultIndexer
from vaultpub.core.navigation_order import (
    NavigationOrderConflict,
    order_editor_payload,
    reset_navigation_order,
    save_navigation_order,
)


def test_save_order_keeps_content_and_non_visible_entries(tmp_path) -> None:
    (tmp_path / "Guides").mkdir()
    (tmp_path / "Guides" / "README.md").write_text("# Guides", encoding="utf-8")
    (tmp_path / "A.md").write_text("# A", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B", encoding="utf-8")
    (tmp_path / "Pinned.md").write_text("# Pinned", encoding="utf-8")
    (tmp_path / "Hidden.md").write_text("---\npublish: false\n---\n# Hidden", encoding="utf-8")
    order_path = tmp_path / "__order__.json"
    order_path.write_text('["Hidden.md", "B.md", "Guides/"]', encoding="utf-8")
    (tmp_path / "__star__.json").write_text('["Pinned.md"]', encoding="utf-8")

    config = PublisherConfig(vault_path=tmp_path, realtime=False)
    index = VaultIndexer(config).build()
    payload = order_editor_payload(config, index)

    assert payload["pinned"] == [{"token": "Pinned.md", "label": "Pinned.md"}]
    assert payload["folders"] == [{"token": "Guides/", "label": "Guides"}]
    assert [item["token"] for item in payload["files"]] == ["B.md", "A.md"]

    save_navigation_order(
        config,
        index,
        ".",
        ["Guides/"],
        ["A.md", "B.md"],
        payload["revision"],
    )

    assert json.loads(order_path.read_text(encoding="utf-8")) == [
        "Pinned.md",
        "Guides/",
        "A.md",
        "B.md",
        "Hidden.md",
    ]
    assert (tmp_path / "A.md").read_text(encoding="utf-8") == "# A"
    assert (tmp_path / "Guides").is_dir()

    refreshed = VaultIndexer(config).build()
    next_payload = order_editor_payload(config, refreshed)
    reset_navigation_order(config, refreshed, ".", next_payload["revision"])
    assert not order_path.exists()
    assert (tmp_path / "B.md").exists()


def test_save_order_rejects_a_stale_revision(tmp_path) -> None:
    (tmp_path / "A.md").write_text("# A", encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path, realtime=False)
    index = VaultIndexer(config).build()
    payload = order_editor_payload(config, index)
    (tmp_path / "__order__.json").write_text('["A.md"]', encoding="utf-8")

    with pytest.raises(NavigationOrderConflict):
        save_navigation_order(config, index, ".", [], ["A.md"], payload["revision"])
