from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mage-doc-backend",
        "version": "0.1.0",
    }


def test_api_status() -> None:
    response = TestClient(app).get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mage-doc-backend"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
