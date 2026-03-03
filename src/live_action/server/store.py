from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        target = self._root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    def load_json(self, relative_path: str) -> dict[str, Any] | None:
        target = self._root / relative_path
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))

    def glob(self, pattern: str) -> list[Path]:
        return sorted(self._root.glob(pattern))

