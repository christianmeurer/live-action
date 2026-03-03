from __future__ import annotations

import os
from hmac import compare_digest

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("LIVE_ACTION_API_KEY", "").strip()
    if expected == "":
        return
    if x_api_key is None or not compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

