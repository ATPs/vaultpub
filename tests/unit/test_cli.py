"""Tests for the vaultpub command-line interface."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from vaultpub.cli.main import app


def _capture_serve_config(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_create_app(config):  # type: ignore[no-untyped-def]
        captured["config"] = config
        return SimpleNamespace(state=SimpleNamespace(vaultpub_state=None))

    monkeypatch.setattr("vaultpub.web.create_app", fake_create_app)
    monkeypatch.setattr("uvicorn.Server.run", lambda self: None)
    return captured


def test_serve_help_shows_all_interface_host_default() -> None:
    result = CliRunner().invoke(app, ["serve", "--help"])

    assert result.exit_code == 0, result.output
    assert "[default: 0.0.0.0]" in result.output


def test_serve_keeps_yaml_include_folders_without_sub_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "Configured").mkdir()
    config_path = tmp_path / "vaultpub.yml"
    config_path.write_text("publish:\n  include_folders:\n    - Configured\n", encoding="utf-8")
    captured = _capture_serve_config(monkeypatch)

    result = CliRunner().invoke(app, ["serve", "--vault", str(tmp_path), "--config", str(config_path)])

    assert result.exit_code == 0, result.output
    config = captured["config"]
    assert config.include_folders == ("Configured",)
    assert config.include_all_attachments is False


def test_serve_sub_path_overrides_yaml_scope_and_deduplicates(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "Configured").mkdir()
    (tmp_path / "Shared").mkdir()
    (tmp_path / "Docs").mkdir()
    config_path = tmp_path / "vaultpub.yml"
    config_path.write_text("publish:\n  include_folders:\n    - Configured\n", encoding="utf-8")
    captured = _capture_serve_config(monkeypatch)

    result = CliRunner().invoke(
        app,
        [
            "serve",
            "--vault",
            str(tmp_path),
            "--config",
            str(config_path),
            "--sub-path",
            "Shared",
            "--sub-path",
            "Docs",
            "--sub-path",
            "Shared",
        ],
    )

    assert result.exit_code == 0, result.output
    config = captured["config"]
    assert config.include_folders == ("Shared", "Docs")
    assert config.include_all_attachments is True


def test_serve_sub_path_dot_selects_vault_root(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture_serve_config(monkeypatch)

    result = CliRunner().invoke(app, ["serve", "--vault", str(tmp_path), "--sub-path", "."])

    assert result.exit_code == 0, result.output
    config = captured["config"]
    assert config.include_folders == (".",)
    assert config.include_all_attachments is True


@pytest.mark.parametrize("sub_path", ["../outside", "/tmp", "missing"])
def test_serve_rejects_invalid_sub_path(tmp_path, sub_path: str) -> None:
    result = CliRunner().invoke(app, ["serve", "--vault", str(tmp_path), "--sub-path", sub_path])

    assert result.exit_code != 0
    assert "--sub-path" in result.output
