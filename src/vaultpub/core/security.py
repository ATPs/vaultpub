from __future__ import annotations

from pathlib import Path

from vaultpub.core.paths import safe_join


def validate_vault_access(vault_root: Path, rel_path: str, follow_symlinks: bool = False) -> Path:
    """Validate and return a safe path within the vault.

    Raises PathTraversalError if the path escapes the vault root.
    """
    return safe_join(vault_root, rel_path)


def is_path_public(rel_path: str, config: object) -> bool:
    """Check if a relative path should be publicly accessible.

    Hidden files, .obsidian/, .git/, metadata.json etc. are never public.
    """
    pp = rel_path.replace("\\", "/")
    parts = pp.split("/")

    forbidden = {".git", ".obsidian", "metadata.json", ".vaultpub.yml", ".obsidian-publish.yml"}
    if pp in forbidden or parts[-1] in forbidden or any(part in forbidden for part in parts):
        return False

    hidden_file_access = bool(getattr(config, "hidden_file_access", False))
    return all(
        not (part.startswith(".") and part not in (".", "..") and not hidden_file_access)
        for part in parts
    )
