from __future__ import annotations

import json
from pathlib import Path


def final_case_status(runs: list[dict]) -> str:
    if not runs:
        return 'DONE'
    failures = sum(int(item.get('exit_code', 0)) != 0 for item in runs)
    if failures == len(runs):
        return 'FAILED'
    if failures:
        return 'DONE_WITH_WARNINGS'
    return 'DONE'


def _read_runs(path: Path) -> list[dict]:
    runs: list[dict] = []
    if not path.exists():
        return runs
    for line in path.read_text(errors='ignore').splitlines():
        if not line.strip():
            continue
        parts = line.split('\t', 1)
        if len(parts) != 2:
            continue
        tool, raw_code = parts
        try:
            code = int(raw_code)
        except ValueError:
            code = 1
        runs.append({
            'tool': tool.strip(),
            'exit_code': code,
            'status': 'OK' if code == 0 else 'ERROR',
        })
    return runs


def finalize_case_tool_runs(case_dir: str | Path) -> dict:
    case = Path(case_dir)
    runs = _read_runs(case / '.tool-status.tsv')
    status = final_case_status(runs)
    (case / 'tool_runs.json').write_text(json.dumps(runs, indent=2, ensure_ascii=False) + '\n')

    meta_path = case / 'meta.json'
    try:
        meta = json.loads(meta_path.read_text())
    except Exception:
        meta = {'case_id': case.name}
    meta['status'] = status
    meta['tool_runs'] = runs
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    return {'status': status, 'tool_runs': runs}
