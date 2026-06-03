"""Integration tests for StaticSiteBuilder."""
from __future__ import annotations

import tempfile
from pathlib import Path

from vaultpub.core.config import PublisherConfig
from vaultpub.core.export import StaticSiteBuilder


def test_build_static_site(vault_basic) -> None:
    config = PublisherConfig(vault_path=vault_basic)
    builder = StaticSiteBuilder(config)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "public"
        result = builder.build(out)
        assert result.pages_written > 0
        assert (out / "index.html").exists()
        assert (out / "search-index.json").exists()
        assert (out / "graph.json").exists()
        assert (out / "robots.txt").exists()
