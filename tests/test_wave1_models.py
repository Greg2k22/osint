from osint_workbench.models.scan import ScanRequest, validate_scan_request
from osint_workbench.models.case import CaseMeta
from osint_workbench.models.evidence import Evidence


def test_passive_domain_request_is_valid():
    request = ScanRequest(type="DOMAIN", target="Example.COM", active=False, authorized=False)
    normalized = validate_scan_request(request)
    assert normalized.type == "DOMAIN"
    assert normalized.target == "Example.COM"


def test_active_requires_authorization():
    request = ScanRequest(type="DOMAIN", target="example.com", active=True, authorized=False)
    try:
        validate_scan_request(request)
    except ValueError as exc:
        assert "authorization" in str(exc).lower()
    else:
        raise AssertionError("ACTIVE without authorization must fail")


def test_active_is_domain_only():
    request = ScanRequest(type="PERSON", target="testuser", active=True, authorized=True)
    try:
        validate_scan_request(request)
    except ValueError as exc:
        assert "domain" in str(exc).lower()
    else:
        raise AssertionError("ACTIVE PERSON must fail")


def test_case_meta_accepts_required_fields():
    case = CaseMeta(case_id="case-1", type="EMAIL", target="a@example.com", mode="PASSIVE", status="DONE")
    assert case.case_id == "case-1"


def test_evidence_keeps_source_identity():
    evidence = Evidence(type="PROFILE_CANDIDATE", value="https://example.com/u/x", collector="sherlock", source_group="sherlock", case_id="case-1")
    assert evidence.confidence == "UNVERIFIED"
    assert evidence.source_group == "sherlock"
