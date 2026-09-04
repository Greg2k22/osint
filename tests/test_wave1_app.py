from fastapi.testclient import TestClient
from osint_workbench.app import create_app


def test_app_exposes_existing_routes():
    app = create_app()
    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/ui" in paths
    assert "/api/cases" in paths
    assert "/api/cases/{case_id}" in paths
    assert "/api/scan" in paths
    assert "/api/jobs" in paths
    assert "/api/v1/runs/validate" in paths


def test_health_is_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ui_is_served():
    client = TestClient(create_app())
    response = client.get("/ui")
    assert response.status_code == 200
    assert "OSINT Workbench" in response.text
