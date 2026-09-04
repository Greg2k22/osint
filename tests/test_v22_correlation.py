import json
from pathlib import Path

from osint_workbench.services.correlation_service import canonical_evidence_key, related_cases, search_cases
from osint_workbench.services.source_quality import annotate_evidence, source_families


def write_case(root: Path, case_id: str, *, target: str, case_type: str, evidence: list[dict]):
    case = root / case_id
    case.mkdir(parents=True)
    (case / "meta.json").write_text(json.dumps({"case_id": case_id, "target": target, "type": case_type, "status": "DONE"}))
    (case / "evidence.json").write_text(json.dumps(evidence))
    return case


def test_canonical_evidence_key_is_type_aware():
    assert canonical_evidence_key({"type": "EMAIL", "value": " User@Example.COM "}) == "EMAIL:user@example.com"
    assert canonical_evidence_key({"type": "DOMAIN", "value": "Example.COM."}) == "DOMAIN:example.com"
    assert canonical_evidence_key({"type": "IP", "value": "192.0.2.10"}) == "IP:192.0.2.10"
    assert canonical_evidence_key({"type": "PROFILE_CANDIDATE", "value": "HTTPS://Example.COM/User"}) == "PROFILE_CANDIDATE:https://example.com/User"


def test_related_cases_rank_by_shared_evidence(tmp_path: Path):
    write_case(tmp_path, "case-a", target="alice", case_type="PERSON", evidence=[
        {"type": "EMAIL", "value": "alice@example.com", "confidence": "HIGH", "sources": ["holehe"]},
        {"type": "PROFILE_CANDIDATE", "value": "https://github.com/alice", "confidence": "MEDIUM", "sources": ["sherlock"]},
    ])
    write_case(tmp_path, "case-b", target="alice@example.com", case_type="EMAIL", evidence=[
        {"type": "EMAIL", "value": "ALICE@example.com", "confidence": "HIGH", "sources": ["holehe"]},
        {"type": "PROFILE_CANDIDATE", "value": "https://github.com/alice", "confidence": "MEDIUM", "sources": ["maigret"]},
    ])
    write_case(tmp_path, "case-c", target="other.org", case_type="DOMAIN", evidence=[
        {"type": "DOMAIN", "value": "other.org", "confidence": "HIGH", "sources": ["subfinder"]},
    ])

    result = related_cases("case-a", tmp_path)
    assert [x["case_id"] for x in result] == ["case-b"]
    assert result[0]["shared_count"] == 2
    assert len(result[0]["shared"]) == 2


def test_search_cases_matches_meta_and_evidence(tmp_path: Path):
    write_case(tmp_path, "case-a", target="alice", case_type="PERSON", evidence=[
        {"type": "EMAIL", "value": "alice@example.com", "confidence": "HIGH", "sources": ["holehe"]},
    ])
    write_case(tmp_path, "case-b", target="example.org", case_type="DOMAIN", evidence=[])

    assert [x["case_id"] for x in search_cases("ALICE@EXAMPLE.COM", tmp_path)] == ["case-a"]
    assert [x["case_id"] for x in search_cases("example.org", tmp_path)] == ["case-b"]


def test_source_family_annotation_counts_independence():
    evidence = [{
        "type": "PROFILE_CANDIDATE",
        "value": "https://example.test/u",
        "sources": ["sherlock", "maigret", "holehe"],
        "confidence": "MEDIUM",
    }]
    annotated = annotate_evidence(evidence)
    assert annotated[0]["source_families"] == ["account-discovery", "email-registration"]
    assert annotated[0]["independent_source_count"] == 2
    assert evidence[0].get("source_families") is None
    assert source_families(["subfinder", "theharvester", "httpx"]) == ["dns-discovery", "web-probing"]
