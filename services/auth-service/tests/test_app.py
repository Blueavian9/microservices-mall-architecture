"""Route tests with no real Postgres or NATS — health, 401 guards, security headers."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "auth-service"
    assert "timestamp" in body
    assert isinstance(body["uptime"], (int, float))


def test_auth_verify_without_bearer():
    assert client.get("/auth/verify").status_code == 401


def test_api_auth_verify_without_bearer():
    assert client.get("/api/auth/verify").status_code == 401


def test_helmet_like_headers_on_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"


def test_metrics_prometheus_text():
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    assert b"http_requests_total" in res.content
