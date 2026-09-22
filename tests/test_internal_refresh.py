import importlib

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from backend.config import get_settings

_VALID = "a" * 32


@pytest.fixture(autouse=True)
def _restore_api_after_reload():
    yield
    get_settings.cache_clear()
    import backend.api as api_mod

    importlib.reload(api_mod)


def _client(monkeypatch, token: str | None = "") -> TestClient:
    if token is None:
        monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    else:
        monkeypatch.setenv("REFRESH_TOKEN", token)
    monkeypatch.setenv("SERVE_FRONTEND", "false")
    get_settings.cache_clear()
    import backend.api as api_mod

    importlib.reload(api_mod)
    return TestClient(api_mod.app)


def test_refresh_route_hidden_without_token(monkeypatch):
    client = _client(monkeypatch, None)
    assert client.post("/internal/refresh", json={"source": "all"}).status_code == 404


def test_refresh_route_hidden_with_short_token(monkeypatch):
    client = _client(monkeypatch, "too-short")
    assert client.post("/internal/refresh", json={"source": "all"}).status_code == 404


def test_refresh_requires_bearer(monkeypatch):
    client = _client(monkeypatch, _VALID)
    assert client.post("/internal/refresh", json={"source": "all"}).status_code == 401


def test_refresh_rejects_wrong_bearer(monkeypatch):
    client = _client(monkeypatch, _VALID)
    resp = client.post(
        "/internal/refresh",
        json={"source": "all"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_refresh_accepts_valid_bearer(monkeypatch):
    pipeline = MagicMock()
    monkeypatch.setattr("backend.routers.admin.run_pipeline", pipeline)
    client = _client(monkeypatch, _VALID)
    resp = client.post(
        "/internal/refresh",
        json={"source": "all"},
        headers={"Authorization": f"Bearer {_VALID}"},
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "running"
    pipeline.assert_called_once()
