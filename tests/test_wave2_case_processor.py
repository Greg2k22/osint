import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "case-v2.py"


def run_processor(case: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run(["python3", str(SCRIPT), str(case)], check=True, env=env, capture_output=True, text=True)


def test_person_legacy_case_is_rescored_and_bundled(tmp_path):
    case = tmp_path / "person-test-1"
    case.mkdir()
    (case / "meta.json").write_text(json.dumps({"type": "PERSON", "username": "test"}))
    (case / "profiles.json").write_text(json.dumps([
        {"username": "test", "url": "https://x.test/test", "sources": ["sherlock", "maigret"], "confidence": "HIGH"}
    ]))
    run_processor(case)
    profiles = json.loads((case / "profiles.json").read_text())
    meta = json.loads((case / "meta.json").read_text())
    assert profiles[0]["confidence"] == "MEDIUM"
    assert profiles[0]["type"] == "PROFILE_CANDIDATE"
    assert meta["schema_version"] == 2
    assert (case / "evidence.json").exists()


def test_email_single_source_is_low(tmp_path):
    case = tmp_path / "email-a-1"
    case.mkdir()
    (case / "meta.json").write_text(json.dumps({"type": "EMAIL", "email": "a@example.com"}))
    (case / "services.json").write_text(json.dumps([
        {"email": "a@example.com", "service": "GitHub", "source": "holehe", "status": "FOUND", "confidence": "MEDIUM"}
    ]))
    run_processor(case)
    services = json.loads((case / "services.json").read_text())
    assert services[0]["confidence"] == "LOW"
