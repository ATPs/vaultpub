from __future__ import annotations

from vaultpub.core.config import PublisherConfig
from vaultpub.core.realtime.watcher import _classify_changes


def test_classify_changes_uses_canonical_attachment_url(tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_text("fake image", encoding="utf-8")
    config = PublisherConfig(vault_path=tmp_path)

    event = _classify_changes({("modified", str(image_path))}, tmp_path, config)

    assert len(event.changed) == 1
    assert event.changed[0].kind == "attachment"
    assert event.changed[0].url == "/assets/image.png"
