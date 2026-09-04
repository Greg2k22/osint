import json
import time
from pathlib import Path

from osint_workbench.services.system_status import runner_status, read_collectors_snapshot
from osint_workbench.services.tool_runs import final_case_status


def test_runner_status_is_ok_for_recent_heartbeat(tmp_path: Path):
    heartbeat = tmp_path / 'runner.heartbeat'
    heartbeat.write_text('ok\n')
    assert runner_status(heartbeat, now=time.time(), max_age=120)['status'] == 'OK'


def test_runner_status_is_error_for_stale_heartbeat(tmp_path: Path):
    heartbeat = tmp_path / 'runner.heartbeat'
    heartbeat.write_text('ok\n')
    old = time.time() - 300
    heartbeat.touch()
    import os
    os.utime(heartbeat, (old, old))
    result = runner_status(heartbeat, now=time.time(), max_age=120)
    assert result['status'] == 'ERROR'
    assert result['age_seconds'] >= 299


def test_collectors_snapshot_defaults_to_not_configured(tmp_path: Path):
    result = read_collectors_snapshot(tmp_path / 'missing.json')
    assert result['bbot']['status'] == 'NOT_CONFIGURED'
    assert result['holehe']['status'] == 'NOT_CONFIGURED'


def test_collectors_snapshot_is_loaded(tmp_path: Path):
    p = tmp_path / 'collectors.json'
    p.write_text(json.dumps({'bbot': {'status': 'OK', 'version': '3.0.2'}}))
    result = read_collectors_snapshot(p)
    assert result['bbot']['version'] == '3.0.2'
    assert result['subfinder']['status'] == 'NOT_CONFIGURED'


def test_final_case_status_reports_warnings_for_partial_tool_failure():
    runs = [
        {'tool': 'maigret', 'exit_code': 0},
        {'tool': 'sherlock', 'exit_code': 1},
    ]
    assert final_case_status(runs) == 'DONE_WITH_WARNINGS'
    assert final_case_status([{'tool': 'holehe', 'exit_code': 0}]) == 'DONE'
    assert final_case_status([{'tool': 'holehe', 'exit_code': 1}]) == 'FAILED'
