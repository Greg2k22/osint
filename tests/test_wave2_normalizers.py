from osint_workbench.services.normalizers.domain import normalize_domain_records
from osint_workbench.services.normalizers.person import normalize_profile_records
from osint_workbench.services.normalizers.email import normalize_email_records


def test_domain_normalizer_deduplicates_and_rejects_out_of_scope():
    records = [
        {"host": "WWW.Example.COM.", "source": "subfinder", "resolved_ips": ["192.0.2.1"]},
        {"host": "www.example.com", "source": "bbot:crt_db", "resolved_ips": ["192.0.2.1", "192.0.2.2"]},
        {"host": "evil-example.com", "source": "theharvester"},
    ]
    result = normalize_domain_records("Example.COM", records)
    assert [x["host"] for x in result] == ["example.com", "www.example.com"]
    host = result[1]
    assert host["confidence"] == "MEDIUM"
    assert host["independent_sources"] == ["bbot", "subfinder"]
    assert host["resolved_ips"] == ["192.0.2.1", "192.0.2.2"]


def test_person_normalizer_marks_single_tool_as_low_candidate():
    result = normalize_profile_records("TestUser", [
        {"url": "https://example.test/TestUser", "source": "sherlock"},
        {"url": "https://example.test/TestUser", "source": "sherlock"},
    ])
    assert len(result) == 1
    assert result[0]["type"] == "PROFILE_CANDIDATE"
    assert result[0]["confidence"] == "LOW"


def test_person_normalizer_correlates_independent_tools():
    result = normalize_profile_records("testuser", [
        {"url": "https://example.test/testuser", "source": "sherlock"},
        {"url": "https://example.test/testuser", "source": "maigret"},
    ])
    assert result[0]["confidence"] == "MEDIUM"


def test_email_normalizer_does_not_turn_absence_into_nonexistence():
    assert normalize_email_records("a@example.com", []) == []


def test_email_normalizer_deduplicates_found_services():
    result = normalize_email_records("A@Example.com", [
        {"service": "GitHub", "source": "holehe", "status": "FOUND"},
        {"service": "github", "source": "holehe", "status": "FOUND"},
    ])
    assert len(result) == 1
    assert result[0]["email"] == "a@example.com"
    assert result[0]["status"] == "FOUND"
    assert result[0]["confidence"] == "LOW"
