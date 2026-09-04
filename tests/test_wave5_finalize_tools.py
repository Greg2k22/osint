import json
from pathlib import Path

from osint_workbench.services.tool_runs import finalize_case_tool_runs


def test_finalize_case_tool_runs_writes_warning_status(tmp_path: Path):
    (tmp_path / 'meta.json').write_text(json.dumps({'case_id': 'c1', 'status': 'DONE'}))
    status_file = tmp_path / '.tool-status.tsv'
    status_file.write_text('maigret\t0\nsherlock\t1\n')

    result = finalize_case_tool_runs(tmp_path)

    assert result['status'] == 'DONE_WITH_WARNINGS'
    runs = json.loads((tmp_path / 'tool_runs.json').read_text())
    assert runs == [
        {'tool': 'maigret', 'exit_code': 0, 'status': 'OK'},
        {'tool': 'sherlock', 'exit_code': 1, 'status': 'ERROR'},
    ]
    meta = json.loads((tmp_path / 'meta.json').read_text())
    assert meta['status'] == 'DONE_WITH_WARNINGS'
