from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from live_action.server.main import app


def test_health_is_public() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVE_ACTION_API_KEY", "secret")
    try:
        client = TestClient(app)
        unauthorized = client.get("/metrics")
        assert unauthorized.status_code == 401

        authorized = client.get("/metrics", headers={"x-api-key": "secret"})
        assert authorized.status_code == 200
        payload = authorized.json()
        assert "jobs_enqueued" in payload
        assert "jobs_completed" in payload
        assert "jobs_failed" in payload
        assert "total_processing_ms" in payload
    finally:
        monkeypatch.delenv("LIVE_ACTION_API_KEY", raising=False)


def test_job_lifecycle_with_idempotent_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LIVE_ACTION_API_KEY", "secret")
    monkeypatch.setattr(
        "live_action.server.orchestrator.inspect_video",
        lambda _: {"format": {"duration": "2.0"}},
    )
    try:
        source = tmp_path / "input.mp4"
        source.write_bytes(b"dummy")

        client = TestClient(app)
        headers = {"x-api-key": "secret"}
        payload = {
            "request_id": "idem-001",
            "input_path": str(source),
            "config": {
                "translation": {"execution_mode": "dry-run"},
                "upscale": {"enabled": False, "execution_mode": "dry-run"},
            },
        }

        first = client.post("/jobs", json=payload, headers=headers)
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["request_id"] == "idem-001"
        assert first_body["run_id"]
        assert first_body["job_id"]

        second = client.post("/jobs", json=payload, headers=headers)
        assert second.status_code == 200
        second_body = second.json()
        assert second_body["run_id"] == first_body["run_id"]
        assert second_body["job_id"] == first_body["job_id"]

        job_response = client.get(f"/jobs/{first_body['job_id']}", headers=headers)
        assert job_response.status_code == 200

        run_response = client.get(f"/runs/{first_body['run_id']}", headers=headers)
        assert run_response.status_code == 200
        run_payload = run_response.json()
        assert run_payload["run_id"] == first_body["run_id"]
        assert isinstance(run_payload["chunks"], list)

        list_response = client.get("/runs", headers=headers)
        assert list_response.status_code == 200
        assert any(item["run_id"] == first_body["run_id"] for item in list_response.json())
    finally:
        monkeypatch.delenv("LIVE_ACTION_API_KEY", raising=False)

