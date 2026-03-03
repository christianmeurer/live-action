from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

from live_action.server.auth import require_api_key


def test_require_api_key_allows_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIVE_ACTION_API_KEY", raising=False)
    require_api_key(None)


def test_require_api_key_rejects_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVE_ACTION_API_KEY", "secret")
    with pytest.raises(HTTPException):
        require_api_key("wrong")


def test_require_api_key_accepts_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVE_ACTION_API_KEY", "secret")
    require_api_key("secret")

