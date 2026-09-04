import json
from osint_workbench.services.case_service import write_case_bundle


def test_case_bundle_writes_v2_structure(tmp_path):
    case_dir = tmp_path / "case-1"
    write_case_bundle(
        case_dir,
        meta={"case_id": "case-1", "type": "DOMAIN", "target": "example.com", "mode": "PASSIVE", "status": "DONE"},
        normalized=[{"type": "HOST", "value": "www.example.com", "confidence": "LOW", "sources": ["subfinder"]}],
        evidence=[{"id": "ev-1", "type": "HOST", "value": "www.example.com", "source": "subfinder"}],
        findings=[],
    )
    assert (case_dir / "raw").is_dir()
    assert (case_dir / "normalized").is_dir()
    assert json.loads((case_dir / "meta.json").read_text())["target"] == "example.com"
    assert json.loads((case_dir / "evidence.json").read_text())[0]["id"] == "ev-1"
    assert json.loads((case_dir / "normalized" / "records.json").read_text())[0]["type"] == "HOST"
