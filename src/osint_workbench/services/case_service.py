import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_case_bundle(case_dir: str | Path, *, meta: dict, normalized: list[dict], evidence: list[dict], findings: list[dict]) -> None:
    case = Path(case_dir)
    (case / "raw").mkdir(parents=True, exist_ok=True)
    (case / "normalized").mkdir(parents=True, exist_ok=True)
    (case / "logs").mkdir(parents=True, exist_ok=True)
    _write_json(case / "meta.json", meta)
    _write_json(case / "normalized" / "records.json", normalized)
    _write_json(case / "evidence.json", evidence)
    _write_json(case / "findings.json", findings)
