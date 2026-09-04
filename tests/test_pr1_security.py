import csv
import io

from fastapi.testclient import TestClient

import osint_workbench.api.scans as scans_api
from osint_workbench.app import create_app
from osint_workbench.services.report_service import render_csv


def test_active_scan_requires_server_side_token(monkeypatch, tmp_path):
    monkeypatch.setattr(scans_api, "JOBS_PENDING", tmp_path)

    client = TestClient(create_app())
    payload = {
        "type": "DOMAIN",
        "target": "example.org",
        "active": True,
        "authorized": True,
    }

    monkeypatch.delenv("OSINT_ACTIVE_TOKEN", raising=False)
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 403

    monkeypatch.setenv("OSINT_ACTIVE_TOKEN", "server-secret")

    response = client.post("/api/scan", json=payload)
    assert response.status_code == 403

    response = client.post(
        "/api/scan",
        json=payload,
        headers={"X-OSINT-Active-Token": "wrong-secret"},
    )
    assert response.status_code == 403

    response = client.post(
        "/api/scan",
        json=payload,
        headers={"X-OSINT-Active-Token": "server-secret"},
    )
    assert response.status_code == 202

    job = response.json()
    assert job["active"] is True
    assert job["authorized"] is True

    # Token nie może trafić do pliku joba.
    saved = (tmp_path / f'{job["id"]}.json').read_text()
    assert "server-secret" not in saved


def test_passive_scan_does_not_require_active_token(monkeypatch, tmp_path):
    monkeypatch.setattr(scans_api, "JOBS_PENDING", tmp_path)
    monkeypatch.delenv("OSINT_ACTIVE_TOKEN", raising=False)

    response = TestClient(create_app()).post(
        "/api/scan",
        json={
            "type": "DOMAIN",
            "target": "example.org",
            "active": False,
            "authorized": False,
        },
    )

    assert response.status_code == 202


def test_csv_export_neutralizes_formula_injection():
    report = {
        "case": {"case_id": "case-1"},
        "high": [
            {
                "type": "=1+1",
                "value": "=HYPERLINK(\"https://example.org\",\"click\")",
                "confidence": "HIGH",
                "sources": ["@external"],
            },
            {
                "type": "PROFILE",
                "value": "\t+SUM(1,1)",
                "confidence": "HIGH",
                "sources": ["source"],
            },
        ],
        "medium": [],
        "low": [],
        "seed": [],
    }

    rows = list(csv.reader(io.StringIO(render_csv(report))))

    # Każda niebezpieczna komórka musi zostać potraktowana jako tekst.
    assert rows[1][0].startswith("'=")
    assert rows[1][1].startswith("'=")
    assert rows[1][3].startswith("'@")
    assert rows[2][1].startswith("'\t+")


def test_ui_sends_active_token_as_header():
    js = open("src/osint_workbench/web/app.js", encoding="utf-8").read()

    assert "X-OSINT-Active-Token" in js
    assert "OSINT_ACTIVE_TOKEN" not in js
