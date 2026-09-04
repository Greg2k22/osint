import json
from pathlib import Path

from osint_workbench.services.report_service import build_report_from_case, render_markdown


def test_report_contains_tool_run_warnings(tmp_path: Path):
    (tmp_path / 'meta.json').write_text(json.dumps({'case_id': 'c', 'status': 'DONE_WITH_WARNINGS'}))
    (tmp_path / 'evidence.json').write_text('[]')
    (tmp_path / 'findings.json').write_text('[]')
    (tmp_path / 'tool_runs.json').write_text(json.dumps([{'tool': 'sherlock', 'exit_code': 1, 'status': 'ERROR'}]))
    report = build_report_from_case(tmp_path)
    assert report['tool_runs'][0]['tool'] == 'sherlock'
    assert 'sherlock: ERROR' in render_markdown(report)
