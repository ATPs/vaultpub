"""Tests for the vaultpub command-line interface."""
from __future__ import annotations

import json
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


def test_serve_accepts_a_markdown_file_and_selects_only_it(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    note = tmp_path / "Only.md"
    note.write_text("# Only", encoding="utf-8")
    captured = _capture_serve_config(monkeypatch)

    result = CliRunner().invoke(app, ["serve", "--vault", str(note)])

    assert result.exit_code == 0, result.output
    config = captured["config"]
    assert config.vault_path == tmp_path.resolve()
    assert config.entry_file == "Only.md"


@pytest.mark.parametrize("option", ["--sub-path", "--home"])
def test_serve_rejects_file_scope_options(tmp_path, monkeypatch: pytest.MonkeyPatch, option: str) -> None:
    note = tmp_path / "Only.md"
    note.write_text("# Only", encoding="utf-8")
    args = ["serve", "--vault", str(note), option, "ignored"]

    result = CliRunner().invoke(app, args)

    assert result.exit_code != 0
    assert option in result.output


def test_build_index_and_doctor_accept_a_markdown_file(tmp_path) -> None:
    note = tmp_path / "Only.md"
    note.write_text("# Only\n\n![[image.png]]\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"png")
    output = tmp_path / "public"
    index_json = tmp_path / "index.json"

    build = CliRunner().invoke(app, ["build", "--vault", str(note), "--out", str(output)])
    index = CliRunner().invoke(app, ["index", "--vault", str(note), "--json", str(index_json)])
    doctor = CliRunner().invoke(app, ["doctor", "--vault", str(note)])

    assert build.exit_code == 0, build.output
    assert index.exit_code == 0, index.output
    assert doctor.exit_code == 0, doctor.output
    assert (output / "Only.md.html").exists()
    assert json.loads(index_json.read_text(encoding="utf-8"))["notes"]
    assert "Notes: 1" in doctor.output


def test_reader_commands_reject_non_markdown_file_input(tmp_path) -> None:
    document = tmp_path / "document.pdf"
    document.write_bytes(b"pdf")

    result = CliRunner().invoke(app, ["doctor", "--vault", str(document)])

    assert result.exit_code != 0
    assert "--vault file must be Markdown" in result.output


@pytest.mark.parametrize("sub_path", ["../outside", "/tmp", "missing"])
def test_serve_rejects_invalid_sub_path(tmp_path, sub_path: str) -> None:
    result = CliRunner().invoke(app, ["serve", "--vault", str(tmp_path), "--sub-path", sub_path])

    assert result.exit_code != 0
    assert "--sub-path" in result.output
