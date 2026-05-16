from pydantic import SecretStr
from fastapi.testclient import TestClient

from code_migration.api.app import app
from code_migration.config import MigrationSettings, settings


def test_healthz_does_not_expose_sensitive_config():
    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    serialized = str(body).lower()
    assert "api_key" not in serialized
    assert "migration_api_key" not in serialized
    assert "c:\\" not in serialized


def test_protected_endpoint_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", SecretStr("local-test-key-with-enough-entropy-123"))
    client = TestClient(app)

    response = client.post("/api/v1/analyze", json={"path": ".", "migration_type": "react-hooks"})

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", SecretStr("local-test-key-with-enough-entropy-123"))
    client = TestClient(app)

    response = client.post(
        "/api/v1/analyze",
        json={"path": ".", "migration_type": "react-hooks"},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_production_rejects_demo_api_key():
    try:
        MigrationSettings(
            api_key=SecretStr("dev-enterprise-key-123"),
            server={
                "environment": "production",
                "host": "127.0.0.1",
                "port": 8000,
                "cors_origins": ["https://example.com"],
                "docs_enabled": False,
            },
        )
    except ValueError as exc:
        assert "demo/default" in str(exc)
    else:
        raise AssertionError("weak production API key was accepted")
