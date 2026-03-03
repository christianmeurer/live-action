from __future__ import annotations

from pathlib import Path

from live_action.server.store import FileStore


def test_store_save_load_and_glob(tmp_path: Path) -> None:
    store = FileStore(tmp_path)
    store.save_json("runs/abc/run-report.json", {"run_id": "abc"})

    loaded = store.load_json("runs/abc/run-report.json")
    assert loaded is not None
    assert loaded["run_id"] == "abc"

    matches = store.glob("runs/*/run-report.json")
    assert len(matches) == 1

