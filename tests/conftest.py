"""Test fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest

from vaultpub.core.config import PublisherConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def vault_basic() -> Path:
    return FIXTURES_DIR / "vault_basic"


@pytest.fixture
def vault_links() -> Path:
    return FIXTURES_DIR / "vault_links"


@pytest.fixture
def vault_obsidian_syntax() -> Path:
    return FIXTURES_DIR / "vault_obsidian_syntax"


@pytest.fixture
def vault_security() -> Path:
    return FIXTURES_DIR / "vault_security"


@pytest.fixture
def vault_publish_filters() -> Path:
    return FIXTURES_DIR / "vault_publish_filters"


@pytest.fixture
def vault_local_resources() -> Path:
    return FIXTURES_DIR / "vault_local_resources"


@pytest.fixture
def basic_config(vault_basic: Path) -> PublisherConfig:
    return PublisherConfig(vault_path=vault_basic)
