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

    for part in parts:
        if part.startswith(".") and part not in (".", ".."):
            return False

    forbidden = {"metadata.json", ".vaultpub.yml", ".obsidian-publish.yml"}
    return not (pp in forbidden or parts[-1] in forbidden)
