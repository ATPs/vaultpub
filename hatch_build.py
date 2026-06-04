from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        frontend_dir = Path(self.root) / "frontend"
        node_modules = frontend_dir / "node_modules"
        npm = shutil.which("npm")
        if npm is None:
            raise RuntimeError("npm is required to build vaultpub frontend assets")

        try:
            subprocess.run([npm, "run", "build"], cwd=frontend_dir, check=True)
        finally:
            shutil.rmtree(node_modules, ignore_errors=True)
