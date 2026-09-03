"""Read and safely update per-directory navigation order controls."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from vaultpub.core.models import NavNode, VaultIndex
from vaultpub.core.paths import safe_join
from vaultpub.core.render.templates import find_nav_directory

ORDER_FILE_NAME = "__order__.json"


class NavigationOrderError(ValueError):
    """Raised when an ordering request cannot be applied."""


class NavigationOrderConflict(NavigationOrderError):
    """Raised when an order file changed after the editor loaded it."""


def order_editor_payload(config: object, index: VaultIndex, directory: str | None = None) -> dict[str, Any]:
    """Return published direct children for one directory without exposing hidden names."""
    selected = _find_directory(index, directory)
    target = _order_file_path(config, selected.path)
    existing, valid = _read_order_entries(target)
    revision = _revision(target)

    children = [child for child in selected.children if not child.nav_hidden]
    pinned = [child for child in children if child.starred]
    movable = [child for child in children if not child.starred]
    if not existing:
        movable = sorted(movable, key=lambda child: (-child.modified_ns, child.label.casefold()))

    folders = [child for child in movable if child.is_dir]
    files = [child for child in movable if not child.is_dir]
    return {
        "directory": selected.path,
        "revision": revision,
        "customOrder": bool(existing) and valid,
        "directories": _directory_choices(index.nav_tree),
        "pinned": [_item(child) for child in pinned],
        "folders": [_item(child) for child in folders],
        "files": [_item(child) for child in files],
    }


def save_navigation_order(
    config: object,
    index: VaultIndex,
    directory: str | None,
    folders: object,
    files: object,
    revision: object,
) -> None:
    """Persist a complete visible order while retaining non-visible legacy entries."""
    selected = _find_directory(index, directory)
    target = _order_file_path(config, selected.path)
    _require_revision(target, revision)

    children = [child for child in selected.children if not child.nav_hidden]
    pinned = [child for child in children if child.starred]
    expected_folders = {_token(child) for child in children if child.is_dir and not child.starred}
    expected_files = {_token(child) for child in children if not child.is_dir and not child.starred}
    folder_tokens = _validate_tokens(folders, expected_folders, "folders")
    file_tokens = _validate_tokens(files, expected_files, "files")

    existing, _valid = _read_order_entries(target)
    visible_tokens = {_token(child) for child in children}
    preserved = [entry for entry in existing if entry not in visible_tokens]
    entries = _unique([*[_token(child) for child in pinned], *folder_tokens, *file_tokens, *preserved])
    _write_order_entries(target, entries)


def reset_navigation_order(config: object, index: VaultIndex, directory: str | None, revision: object) -> None:
    """Remove only the selected directory's order control file."""
    selected = _find_directory(index, directory)
    target = _order_file_path(config, selected.path)
    _require_revision(target, revision)
    try:
        target.unlink(missing_ok=True)
    except OSError as exc:
        raise NavigationOrderError("Unable to remove the custom order") from exc


def _find_directory(index: VaultIndex, directory: str | None) -> NavNode:
    raw = (directory or ".").strip().strip("/") or "."
    selected = find_nav_directory(index.nav_tree, raw)
    if selected is None or selected.nav_hidden:
        raise NavigationOrderError("Directory is not available for ordering")
    return selected


def _order_file_path(config: object, directory: str) -> Path:
    root = Path(getattr(config, "vault_path")).resolve()
    folder = root if directory in ("", ".") else safe_join(root, directory)
    if not folder.is_dir():
        raise NavigationOrderError("Directory no longer exists")
    return folder / ORDER_FILE_NAME


def _read_order_entries(target: Path) -> tuple[list[str], bool]:
    if not target.exists():
        return [], True
    try:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [], False
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        return [], False
    return data, True


def _revision(target: Path) -> str:
    try:
        content = target.read_bytes()
    except FileNotFoundError:
        return "missing"
    except OSError as exc:
        raise NavigationOrderError("Unable to read the custom order") from exc
    return hashlib.sha256(content).hexdigest()


def _require_revision(target: Path, revision: object) -> None:
    if not isinstance(revision, str) or revision != _revision(target):
        raise NavigationOrderConflict("The custom order changed. Reload and try again.")


def _validate_tokens(value: object, expected: set[str], section: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise NavigationOrderError(f"{section.title()} must be a list of names")
    tokens = [item.strip() for item in value]
    if len(tokens) != len(set(tokens)) or set(tokens) != expected:
        raise NavigationOrderError(f"{section.title()} do not match the current directory")
    return tokens


def _write_order_entries(target: Path, entries: list[str]) -> None:
    temp_name: str | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except OSError as exc:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise NavigationOrderError("Unable to save the custom order") from exc


def _directory_choices(node: NavNode | None) -> list[dict[str, str]]:
    if node is None:
        return []
    choices: list[dict[str, str]] = []

    def visit(current: NavNode) -> None:
        if current.nav_hidden:
            return
        choices.append({"path": current.path, "label": "/" if current.path == "." else f"{current.path}/"})
        for child in current.children:
            if child.is_dir:
                visit(child)

    visit(node)
    return choices


def _item(child: NavNode) -> dict[str, str]:
    return {"token": _token(child), "label": child.label}


def _token(child: NavNode) -> str:
    return f"{child.raw_label}{'/' if child.is_dir else ''}"


def _unique(entries: list[str]) -> list[str]:
    return list(dict.fromkeys(entries))
