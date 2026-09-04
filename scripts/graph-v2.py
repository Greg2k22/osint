#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from osint_workbench.services.batch_import import build_case_statements


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def infer_target(meta: dict) -> str:
    return str(meta.get('target') or meta.get('email') or meta.get('username') or '')


def main() -> int:
    cases_root = ROOT / 'data' / 'cases'
    selected = [Path(sys.argv[1])] if len(sys.argv) > 1 else sorted(p for p in cases_root.iterdir() if p.is_dir())
    for case in selected:
        meta = load_json(case / 'meta.json', {})
        records = load_json(case / 'normalized' / 'records.json', [])
        if not meta or not isinstance(records, list):
            continue
        payload = {
            'case_id': meta.get('case_id', case.name),
            'type': str(meta.get('type', '')).upper(),
            'target': infer_target(meta),
            'path': str(case),
        }
        for statement in build_case_statements(payload, records):
            print(statement)
    print('MATCH (c:Case) RETURN count(c) AS cases;')
    print('MATCH (h:Host) RETURN count(h) AS hosts;')
    print('MATCH (p:Profile) RETURN count(p) AS profiles;')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
