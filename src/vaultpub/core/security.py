from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from vaultpub.core.paths import safe_join

ALWAYS_FORBIDDEN = {".git", ".obsidian", "metadata.json", ".vaultpub.yml", ".obsidian-publish.yml"}


def validate_vault_access(vault_root: Path, rel_path: str, follow_symlinks: bool = False) -> Path:
    """Validate and return a safe path within the vault.

    Raises PathTraversalError if the path escapes the vault root.
    """
    return safe_join(vault_root, rel_path)


def is_path_public(rel_path: str, config: object) -> bool:
    """Check if a relative path should be publicly accessible.

    Hidden files, .obsidian/, .git/, metadata.json etc. are never public.
    """
    return not is_path_excluded(rel_path, config)


def is_path_excluded(rel_path: str, config: object) -> bool:
    """Check if a path should be excluded from public access.

    Evaluation order:
    1. Block always-forbidden names.
    2. Block hidden files and folders by default unless hidden_file_access=True.
    3. Apply exclude_folders.
    4. Apply exclude_globs.
    5. Apply force_exclude_regexes.

    Returns True if the path should be excluded.
    """
    pp = rel_path.replace("\\", "/")
    parts = pp.split("/")

    # 1. Always-forbidden names
    if pp in ALWAYS_FORBIDDEN or parts[-1] in ALWAYS_FORBIDDEN:
        return True
    for part in parts:
        if part in ALWAYS_FORBIDDEN:
            return True

    # 2. Hidden files and folders
    hidden_file_access = bool(getattr(config, "hidden_file_access", False))
    if not hidden_file_access:
        for part in parts:
            if part.startswith(".") and part not in (".", ".."):
                return True

    # 3. Exclude folders
    exclude_folders: tuple[str, ...] = getattr(config, "exclude_folders", ())
    if parts[0] in exclude_folders:
        return True

    # 4. Exclude globs
    exclude_globs: tuple[str, ...] = getattr(config, "exclude_globs", ())
    if exclude_globs and any(fnmatch.fnmatch(pp, pat) for pat in exclude_globs):
        return True

    # 5. Force-exclude regexes
    compiled_exclude: list[re.Pattern[str]] = getattr(config, "_compiled_force_exclude", [])
    if compiled_exclude and any(pat.search(pp) for pat in compiled_exclude):
        return True

    return False


def is_force_included(rel_path: str, config: object) -> bool:
    """Check if a non-.md file matches force_include_regexes."""
    compiled_include: list[re.Pattern[str]] = getattr(config, "_compiled_force_include", [])
    if not compiled_include:
        return False
    pp = rel_path.replace("\\", "/")
    return any(pat.search(pp) for pat in compiled_include)


def is_text_file(file_path: Path) -> bool:
    """Check if a file is decodable as UTF-8 text (not binary)."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
        chunk.decode("utf-8-sig")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def infer_language(ext: str) -> str:
    """Infer a code language class from a file extension."""
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".css": "css",
        ".scss": "scss",
        ".html": "html",
        ".xml": "xml",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".sql": "sql",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".jl": "julia",
        ".lua": "lua",
        ".vim": "vim",
        ".tex": "latex",
        ".makefile": "makefile",
        ".dockerfile": "dockerfile",
        ".md": "markdown",
        ".txt": "text",
        ".csv": "csv",
        ".log": "text",
    }
    return lang_map.get(ext.lower(), "")
