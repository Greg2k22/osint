import json

from osint_workbench.services.report_service import build_report_from_case, render_markdown


def test_report_has_executive_summary_and_source_independence(tmp_path):
    (tmp_path / "meta.json").write_text(json.dumps({"case_id": "c1", "target": "alice", "type": "PERSON", "status": "DONE"}))
    (tmp_path / "evidence.json").write_text(json.dumps([
        {"type": "PROFILE_CANDIDATE", "value": "https://example.test/a", "confidence": "HIGH", "sources": ["sherlock", "maigret"]},
        {"type": "EMAIL", "value": "alice@example.com", "confidence": "MEDIUM", "sources": ["holehe"]},
    ]))
    (tmp_path / "findings.json").write_text("[]")
    (tmp_path / "tool_runs.json").write_text(json.dumps([{"tool": "sherlock", "status": "OK", "exit_code": 0}]))

    report = build_report_from_case(tmp_path)
    assert report["summary"]["independent_source_families"] == 2
    assert report["executive_summary"]
    assert report["high"][0]["independent_source_count"] == 1
    md = render_markdown(report)
    assert "## Podsumowanie wykonawcze" in md
    assert "Niezależne rodziny źródeł" in md
