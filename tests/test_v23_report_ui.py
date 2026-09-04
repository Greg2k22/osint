from pathlib import Path

from osint_workbench.services.report_service import build_report_from_case, render_markdown


def test_report_contains_pivot_summary_and_lineage(tmp_path: Path):
    import json
    case = tmp_path / "case-a"
    case.mkdir()
    (case / "meta.json").write_text(json.dumps({"case_id": "case-a", "type": "DOMAIN", "target": "example.org", "status": "DONE"}))
    (case / "evidence.json").write_text(json.dumps([{"type": "USERNAME", "value": "alice", "confidence": "HIGH", "sources": ["sherlock"]}]))
    (case / "findings.json").write_text("[]")
    (case / "tool_runs.json").write_text("[]")
    (case / "pivot_lineage.json").write_text(json.dumps([{"job_id": "j1", "scan_type": "PERSON", "target": "alice", "score": 80, "depth": 1, "reason": "USERNAME evidence"}]))

    report = build_report_from_case(case)
    assert report["pivot_summary"]["enqueued_count"] == 1
    assert report["pivot_lineage"][0]["target"] == "alice"
    md = render_markdown(report)
    assert "Ścieżka dochodzenia" in md
    assert "alice" in md


def test_ui_has_pivot_panel_and_passive_auto_enqueue_action():
    html = Path("src/osint_workbench/web/index.html").read_text(encoding="utf-8")
    js = Path("src/osint_workbench/web/app.js").read_text(encoding="utf-8")
    assert 'id="pivot-panel"' in html
    assert 'id="pivot-list"' in html
    assert 'id="pivot-auto-enqueue"' in html
    assert "loadPivots" in js
    assert "autoEnqueuePivots" in js
    assert "/pivots/auto-enqueue" in js
