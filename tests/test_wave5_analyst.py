from pathlib import Path

from osint_workbench.services.analyst_service import AnalystService, bind_claims_to_evidence


def test_analyst_is_optional_when_provider_is_not_configured(tmp_path: Path):
    (tmp_path / 'evidence.json').write_text('[]')
    result = AnalystService(provider=None).analyze_case(tmp_path)
    assert result == {'status': 'NOT_CONFIGURED', 'claims': []}


def test_claim_without_evidence_is_hypothesis():
    evidence = [{'id': 'ev-1'}]
    claims = [
        {'claim': 'supported', 'evidence_ids': ['ev-1']},
        {'claim': 'unsupported', 'evidence_ids': []},
        {'claim': 'unknown ref', 'evidence_ids': ['ev-999']},
    ]
    result = bind_claims_to_evidence(claims, evidence)
    assert result[0]['classification'] == 'SUPPORTED'
    assert result[1]['classification'] == 'HYPOTHESIS'
    assert result[2]['classification'] == 'HYPOTHESIS'
