import json

from fastapi.testclient import TestClient

import osint_workbench.api.intelligence as intelligence_api
from osint_workbench.app import create_app


def write_case(root, case_id, target, evidence):
    case = root / case_id
    case.mkdir(parents=True)
    (case / "meta.json").write_text(json.dumps({"case_id": case_id, "target": target, "type": "PERSON", "status": "DONE"}))
    (case / "evidence.json").write_text(json.dumps(evidence))


def test_search_and_related_endpoints(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence_api, "CASES_ROOT", tmp_path)
    write_case(tmp_path, "case-a", "alice", [{"type": "EMAIL", "value": "alice@example.com", "sources": ["holehe"]}])
    write_case(tmp_path, "case-b", "alice2", [{"type": "EMAIL", "value": "ALICE@example.com", "sources": ["holehe"]}])

    client = TestClient(create_app())
    response = client.get("/api/search", params={"q": "alice@example.com"})
    assert response.status_code == 200
    assert {x["case_id"] for x in response.json()["cases"]} == {"case-a", "case-b"}

    response = client.get("/api/cases/case-a/related")
    assert response.status_code == 200
    assert response.json()["related"][0]["case_id"] == "case-b"


def test_related_missing_case_is_404(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence_api, "CASES_ROOT", tmp_path)
    response = TestClient(create_app()).get("/api/cases/missing/related")
    assert response.status_code == 404
