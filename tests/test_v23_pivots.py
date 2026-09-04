import json
from pathlib import Path

from fastapi.testclient import TestClient

from osint_workbench.app import create_app
from osint_workbench.services.pivot_service import (
    build_pivot_plan,
    enqueue_pivot,
    pivot_target_from_evidence,
)


def write_case(root: Path, case_id: str, target: str, evidence: list[dict], **meta_extra):
    case = root / case_id
    case.mkdir(parents=True)
    meta = {"case_id": case_id, "type": "DOMAIN", "target": target, "status": "DONE", **meta_extra}
    (case / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (case / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    return case


def test_pivot_target_mapping_is_type_aware():
    assert pivot_target_from_evidence({"type": "DOMAIN", "value": "Sub.Example.org."}) == ("DOMAIN", "sub.example.org")
    assert pivot_target_from_evidence({"type": "EMAIL", "value": "A@Example.org"}) == ("EMAIL", "a@example.org")
    assert pivot_target_from_evidence({"type": "USERNAME", "value": " Alice "}) == ("PERSON", "alice")
    assert pivot_target_from_evidence({"type": "PROFILE", "value": "https://github.com/Alice"}) == ("PERSON", "alice")
    assert pivot_target_from_evidence({"type": "IP", "value": "192.0.2.5"}) is None


def test_plan_scores_and_deduplicates_existing_targets(tmp_path: Path):
    cases = tmp_path / "cases"
    jobs = tmp_path / "jobs"
    for q in ("pending", "running", "done", "failed"):
        (jobs / q).mkdir(parents=True)

    write_case(cases, "case-a", "example.org", [
        {"type": "EMAIL", "value": "alice@example.org", "confidence": "HIGH", "sources": ["holehe"]},
        {"type": "USERNAME", "value": "Alice", "confidence": "MEDIUM", "sources": ["sherlock", "maigret"]},
        {"type": "DOMAIN", "value": "example.org", "confidence": "HIGH", "sources": ["subfinder"]},
    ])
    write_case(cases, "case-b", "alice@example.org", [], type="EMAIL")

    plan = build_pivot_plan("case-a", cases, jobs, max_depth=2, limit=20)
    targets = {(p["scan_type"], p["target"]) for p in plan["pivots"] if p["executable"]}
    assert ("EMAIL", "alice@example.org") not in targets
    assert ("DOMAIN", "example.org") not in targets
    assert ("PERSON", "alice") in targets
    pivot = next(p for p in plan["pivots"] if p.get("target") == "alice")
    assert pivot["score"] >= 50
    assert pivot["depth"] == 1
    assert pivot["parent_case_id"] == "case-a"
    assert pivot["active"] is False


def test_enqueue_writes_passive_job_and_parent_lineage(tmp_path: Path):
    cases = tmp_path / "cases"
    jobs = tmp_path / "jobs"
    for q in ("pending", "running", "done", "failed"):
        (jobs / q).mkdir(parents=True)
    case = write_case(cases, "case-a", "example.org", [
        {"type": "USERNAME", "value": "alice", "confidence": "HIGH", "sources": ["sherlock"]},
    ])

    plan = build_pivot_plan("case-a", cases, jobs, max_depth=2, limit=20)
    pivot = next(p for p in plan["pivots"] if p["executable"])
    result = enqueue_pivot("case-a", pivot["pivot_id"], cases, jobs)

    job = json.loads((jobs / "pending" / f'{result["job_id"]}.json').read_text())
    assert job["active"] is False
    assert job["authorized"] is False
    assert job["pivot_parent_case_id"] == "case-a"
    assert job["pivot_depth"] == 1
    assert job["pivot_id"] == pivot["pivot_id"]

    lineage = json.loads((case / "pivot_lineage.json").read_text())
    assert lineage[-1]["job_id"] == result["job_id"]
    assert lineage[-1]["target"] == "alice"


def test_api_exposes_pivots_and_auto_enqueue_is_bounded(monkeypatch, tmp_path: Path):
    import osint_workbench.api.pivots as pivots_api

    cases = tmp_path / "cases"
    jobs = tmp_path / "jobs"
    for q in ("pending", "running", "done", "failed"):
        (jobs / q).mkdir(parents=True)

    write_case(cases, "case-a", "example.org", [
        {"type": "USERNAME", "value": "alice", "confidence": "HIGH", "sources": ["sherlock", "maigret"]},
        {"type": "EMAIL", "value": "alice@example.org", "confidence": "HIGH", "sources": ["holehe"]},
    ])

    monkeypatch.setattr(pivots_api, "CASES_ROOT", cases)
    monkeypatch.setattr(pivots_api, "JOBS_ROOT", jobs)
    client = TestClient(create_app())

    response = client.get("/api/cases/case-a/pivots")
    assert response.status_code == 200
    assert response.json()["pivots"]

    response = client.post("/api/cases/case-a/pivots/auto-enqueue", json={"min_score": 50, "max_count": 1, "max_depth": 2})
    assert response.status_code == 202
    body = response.json()
    assert len(body["enqueued"]) <= 1
    assert all(item["active"] is False for item in body["enqueued"])


def test_depth_three_never_generates_executable_children(tmp_path: Path):
    cases = tmp_path / "cases"
    jobs = tmp_path / "jobs"
    for q in ("pending", "running", "done", "failed"):
        (jobs / q).mkdir(parents=True)
    write_case(cases, "case-a", "example.org", [
        {"type": "EMAIL", "value": "a@example.org", "confidence": "HIGH", "sources": ["holehe"]},
    ], pivot_depth=3)

    plan = build_pivot_plan("case-a", cases, jobs, max_depth=3, limit=20)
    assert plan["depth_limit_reached"] is True
    assert not any(p["executable"] for p in plan["pivots"])
